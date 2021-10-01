import click
from selfassess.utils import get_session
from selfassess.export.utils import get_participant_sessions
from sqlalchemy import select
from sqlalchemy import func
from selfassess.database import Word
from selfassess.queries import participant_timeline_query, native_language
from selfassess.quali import CEFR_LEVELS
from datetime import date
from tabulate import tabulate
from ordered_set import OrderedSet


def fmt_dt(dt):
    if dt is not None:
        return str(dt).split(".", 1)[0]
    else:
        return "no"


def print_participant(participant_num, lang, total_words, participant):
    print(
        f"Participant #{participant_num} {lang}: "
        f"{participant.given_name} {participant.surname} "
        f"({participant.email})"
    )
    print("  Account\n\tCreated: {}\n\tAccepted: {}\n\tAcceptance deadline: {}".format(
        fmt_dt(participant.create_date),
        fmt_dt(participant.accept_date),
        participant.accept_deadline,
    ))
    print("  Proof\n\tUploaded: {}\n\tProof: {}\n\tAccepted: {}\n\tText: \"{}\"".format(
        fmt_dt(participant.proof_upload_date),
        participant.proof or "no",
        fmt_dt(participant.proof_accept_date),
        participant.text_on_proof
    ))
    sessions = [
        part_session
        for part_session in
        get_participant_sessions(participant, only_selfassess=True)
    ]
    total_mins = int(sum((
        part_session["time"].total_seconds()
        for part_session in sessions
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
        len(sessions)
    ))
    print("  Mini-exam\n\tStarted: {}\n\tFinished: {}\n\tAccepted: {}\n\tCompletion deadline: {}".format(
        fmt_dt(participant.miniexam_start_date),
        fmt_dt(participant.miniexam_finish_date),
        fmt_dt(participant.miniexam_accept_date),
        participant.complete_deadline,
    ))


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


STATUSES_TO_SYMBOLS = {
    "start_overdue": "🪦",
    "finish_overdue": "🪦",
    "almost_overdue": "😟",
    "due_reminder": "⏰",
    "complete": "✔️",
    "started_selfassess": "😄",
    "idle": "😴",
}


def group_participant(participant):
    today = date.today()
    if participant.withdraw_date is not None:
        return "withdrawn"
    elif participant.selfassess_start_date is None:
        if participant.accept_deadline < today:
            return "start_overdue"
        elif participant.accept_deadline == today:
            return "almost_overdue"
        elif (participant.create_date.date() - today).days > 2:
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
        cefr = participant.cefr_proof_reading_comprehension
        self._cefr_build.add(cefr)
        self._lang_build.add(lang)
        self._grid.setdefault((cefr, lang), []).append(sym)

    def __str__(self):
        tab = []
        cefrs = self._cefr_build.build()
        langs = self._lang_build.build()
        tab.append(["", *(CEFR_LEVELS[cefr - 1] for cefr in cefrs)])
        for lang in langs:
            tab.append([
                lang,
                *("".join(self._grid[(cefr, lang)]) for cefr in cefrs)
            ])
        return tabulate(tab, tablefmt="fancy_grid")


@click.command()
@click.option("--ignore", multiple=True)
@click.option("--show-withdrawn/--hide-withdrawn")
def main(ignore, show_withdrawn):
    sqlite_sess = get_session()
    participants = sqlite_sess.execute(participant_timeline_query()).scalars()
    grid_groups = GridAgg()
    status_groups = {status: [] for status in STATUSES}
    for pid, participant in enumerate(participants):
        if participant.email in ignore:
            continue
        lang = sqlite_sess.execute(native_language(participant)).scalars().first().language
        status = group_participant(participant)
        if status in STATUSES_TO_SYMBOLS:
            grid_groups.add(lang, participant, STATUSES_TO_SYMBOLS[status])
        status_groups[status].append((lang, participant))

    total_words = sqlite_sess.execute(
        select(func.count()).select_from(Word)
    ).scalars().first()
    participant_num = 1
    for status_group, status_participants in status_groups.items():
        if status_group == "withdrawn" and not show_withdrawn:
            continue
        sym = STATUSES_TO_SYMBOLS.get(status_group, "*")
        group_title = status_group.title().replace("_", " ")
        print(f" {sym}{sym} {group_title} {sym}{sym} ")
        for lang, participant in status_participants:
            print()
            print_participant(participant_num, lang, total_words, participant)
            participant_num += 1
            print()
        print()
        print()
    print(grid_groups)


if __name__ == "__main__":
    main()
