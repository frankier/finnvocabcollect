import click
from selfassess.database import Participant
from selfassess.utils import get_session
from selfassess.export.utils import get_participant_sessions
from sqlalchemy import select
from sqlalchemy import func
from selfassess.database import Word


def fmt_dt(dt):
    if dt is not None:
        return str(dt)
    else:
        return "no"


@click.command()
def main():
    sqlite_sess = get_session()
    participants = sqlite_sess.query(Participant)
    for pid, participant in enumerate(participants):
        print(
            f"Participant #{pid + 1}: "
            f"{participant.given_name} {participant.surname} "
            f"({participant.email})"
        )
        print("Account created: {}; accepted: {}; acceptance deadline: {}".format(
            participant.create_date,
            fmt_dt(participant.accept_date),
            participant.accept_deadline,
        ))
        print("Proof uploaded: {}; accepted: {}".format(
            fmt_dt(participant.proof_upload_date),
            fmt_dt(participant.proof_accept_date)
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
        total_words = sqlite_sess.execute(
            select(func.count()).select_from(Word)
        ).scalars().first()
        print((
            "Self assessment started: {}; finished: {}; accepted: {}; \n"
            "\tcompleted {}/{} in {} hr {} mins over {} sessions"
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
        print("Mini-exam started: {}; finished: {}; accepted: {}; completion deadline: {}".format(
            fmt_dt(participant.miniexam_start_date),
            fmt_dt(participant.miniexam_finish_date),
            fmt_dt(participant.miniexam_accept_date),
            participant.complete_deadline,
        ))
        print()


if __name__ == "__main__":
    main()
