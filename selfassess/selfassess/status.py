import click
from selfassess.utils import get_session
from selfassess.export.utils import gather_events, events_to_sessions
from sqlalchemy import select
from sqlalchemy import func
from selfassess.database import Word
from selfassess.quali import num_to_cefr
from selfassess.queries import participant_timeline_query, native_language
from datetime import date
from tabulate import tabulate
from ordered_set import OrderedSet


def fmt_dt(dt):
    if dt is not None:
        return str(dt).split(".", 1)[0]
    else:
        return "no"


def participant_cefr(participant):
    return participant.cefr_selfassess_reading_comprehension


def print_participant(lang, total_words, participant):
    selfassess_events = gather_events(participant, only_selfassess=True)
    miniexam_events = gather_events(participant, only_miniexam=True)
    last_timestamp = None
    if len(selfassess_events):
        last_timestamp = selfassess_events[-1][0]
    if len(miniexam_events):
        last_timestamp = miniexam_events[-1][0]
    cefr = num_to_cefr(participant_cefr(participant))
    if participant.given_name:
        name = f" ({participant.given_name} {participant.surname})"
    else:
        name = ""
    print(
        f"#{participant.id:02} {cefr} {lang} {participant.email}" + name
    )
    print("  Last activity: {}".format(fmt_dt(last_timestamp)))
    print("  Account\n\tCreated: {}\n\tAccepted: {}\n\tAcceptance deadline: {}".format(
        fmt_dt(participant.create_date),
        fmt_dt(participant.accept_date),
        participant.accept_deadline,
    ))
    print("  Proof\n\tUploaded: {}\n\tProof: {}\n\tAccepted: {}\n\tText:\n{}".format(
        fmt_dt(participant.proof_upload_date),
        participant.proof or "no",
        fmt_dt(participant.proof_accept_date),
        "\n".join((
            "\t\t" + line
            for line in participant.text_on_proof.split("\n")
        ))
    ))
    selfassess_sessions = events_to_sessions(selfassess_events)
    total_mins = int(sum((
        part_session["time"].total_seconds()
        for part_session in selfassess_sessions
    )) // 60)
    completed_words = participant.next_response
    print((
        "  Self-assessment\n\tStarted: {}\n\tFinished: {}\n\tAccepted: {}\n\t"
        "Completed: {}/{}\n\tTime: {} hr {} mins\n\tSessions: {}"
    ).format(
        fmt_dt(participant.selfassess_start_date),
        fmt_dt(participant.selfassess_finish_date),
        fmt_dt(participant.selfassess_accept_date),
        completed_words,
        total_words,
        total_mins // 60,
        total_mins % 60,
        len(selfassess_sessions)
    ))
    print("  Mini-exam\n\tStarted: {}\n\tFinished: {}\n\tAccepted: {}\n\tCompletion deadline: {}".format(
        fmt_dt(participant.miniexam_start_date),
        fmt_dt(participant.miniexam_finish_date),
        fmt_dt(participant.miniexam_accept_date),
        participant.complete_deadline,
    ))


class StatusBase:
    @classmethod
    def status_to_symbol(cls, status):
        return cls.TO_SYMBOLS.get(status)

    @classmethod
    def with_symbol(cls, participant):
        status = cls.from_participant(participant)
        return status, cls.status_to_symbol(status)


def is_due_reminder(participant, today):
    return (participant.create_date.date() - today).days >= 2


class NormalStatus(StatusBase):
    STATUSES = [
        "start_overdue",
        "finish_overdue",
        "almost_overdue",
        "due_reminder",
        "complete",
        "started_selfassess",
        "idle",
        "withdrawn",
    ]

    TO_SYMBOLS = {
        "start_overdue": "🪦",
        "finish_overdue": "🪦",
        "almost_overdue": "😟",
        "due_reminder": "⏰",
        "complete": "✔️",
        "started_selfassess": "😄",
        "idle": "😴",
    }

    HIDE_DEFAULT = ["withdrawn"]

    @staticmethod
    def from_participant(participant):
        today = date.today()
        if participant.withdraw_date is not None:
            return "withdrawn"
        elif participant.selfassess_start_date is None:
            if participant.accept_deadline < today:
                return "start_overdue"
            elif participant.accept_deadline == today:
                return "almost_overdue"
            elif is_due_reminder(participant, today):
                return "due_reminder"
            else:
                return "idle"
        elif participant.miniexam_finish_date is None:
            if participant.complete_deadline < today:
                return "finish_overdue"
            else:
                return "started_selfassess"
        else:
            return "complete"


class ToActionStatus(StatusBase):
    STATUSES = [
        "to_withdraw",
        "to_approve_proof",
        "to_approve_selfassess",
        "to_approve_miniexam",
        "due_reminder",
        "nothing_due",
        "withdrawn",
    ]

    TO_SYMBOLS = {
        "to_approve_proof": "🛂",
        "to_approve_selfassess": "5️",
        "to_approve_miniexam": "💯",
        "to_withdraw": "🪦",
        "due_reminder": "⏰",
    }

    HIDE_DEFAULT = ["nothing_due", "withdrawn"]

    @staticmethod
    def from_participant(participant):
        today = date.today()
        if participant.withdraw_date is not None:
            return "withdrawn"
        elif (
            participant.accept_deadline < today
            or participant.complete_deadline < today
        ):
            return "to_withdraw"
        elif (
            participant.proof is not None
            and participant.proof_accept_date is None
        ):
            return "to_approve_proof"
        elif (
            participant.selfassess_finish_date is not None
            and participant.selfassess_accept_date is None
        ):
            return "to_approve_selfassess"
        elif (
            participant.miniexam_finish_date is not None
            and participant.miniexam_accept_date is None
        ):
            return "to_approve_selfassess"
        elif is_due_reminder(participant, today):
            return "due_reminder"
        else:
            return "nothing_due"


class IndexBuilder:
    def __init__(self):
        self._builder = set()

    def add(self, elem):
        self._builder.add(elem)

    def build(self):
        return OrderedSet(sorted(self._builder))


class GridAgg:
    def __init__(self):
        self._cefr_build = IndexBuilder()
        self._lang_build = IndexBuilder()
        self._grid = {}

    def add(self, lang, participant, sym):
        cefr = participant_cefr(participant)
        self._cefr_build.add(cefr)
        self._lang_build.add(lang)
        self._grid.setdefault((cefr, lang), []).append(sym)

    def __str__(self):
        tab = []
        cefrs = self._cefr_build.build()
        langs = self._lang_build.build()
        tab.append(["", *(num_to_cefr(cefr) for cefr in cefrs)])
        for lang in langs:
            tab.append([
                lang,
                *(
                    "".join(sorted(self._grid.get((cefr, lang), [])))
                    for cefr in cefrs
                )
            ])
        return tabulate(tab, tablefmt="fancy_grid")


@click.command()
@click.option("--ignore", multiple=True)
@click.option("--show-all/--hide-default")
@click.option("--to-action/--normal-status")
def main(ignore, show_all, to_action):
    if to_action:
        status_cls = ToActionStatus
    else:
        status_cls = NormalStatus
    sqlite_sess = get_session()
    participants = sqlite_sess.execute(participant_timeline_query()).scalars()
    grid_groups = GridAgg()
    status_groups = {status: [] for status in status_cls.STATUSES}
    for pid, participant in enumerate(participants):
        if participant.email in ignore:
            continue
        lang = sqlite_sess.execute(native_language(participant)).scalars().first().language
        status, symbol = status_cls.with_symbol(participant)
        if symbol is not None:
            grid_groups.add(lang, participant, symbol)
        status_groups[status].append((lang, participant))

    total_words = sqlite_sess.execute(
        select(func.count()).select_from(Word)
    ).scalars().first()
    for status_group, status_participants in status_groups.items():
        if status_group in status_cls.HIDE_DEFAULT and not show_all:
            continue
        sym = status_cls.status_to_symbol(status_group) or "*"
        group_title = status_group.title().replace("_", " ")
        print(f" {sym}{sym} {group_title} {sym}{sym} ")
        for lang, participant in status_participants:
            print()
            print_participant(lang, total_words, participant)
            print()
        print()
        print()
    print(grid_groups)


if __name__ == "__main__":
    main()
