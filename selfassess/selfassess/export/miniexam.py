import click
from pandas import DataFrame

from selfassess.database import Participant, MiniexamResponseType
from selfassess.utils import get_session


@click.command()
@click.argument("outf", type=click.Path())
@click.argument("email", nargs=-1)
def main(outf, email):
    session = get_session()
    rows = []
    for em in email:
        participant = session.query(Participant).filter_by(email=em).first()
        responses = 0
        no_responses = 0
        for miniexam_slot in participant.miniexam_slots:
            if miniexam_slot.responses:
                responses += 1
            else:
                no_responses += 1
        for miniexam_slot in participant.miniexam_slots:
            resp = miniexam_slot.responses[-1]
            rows.append((
                participant.id,
                resp.id,
                miniexam_slot.word.word,
                resp.response_lang.name if resp.response_lang is not None else "",
                resp.response_type.name,
                resp.response,
                "1b" if resp.response_type == MiniexamResponseType.donotknow else "",
                ""
            ))
    df = DataFrame.from_records(
        rows,
        columns=("participant_id", "response_id", "word", "lang", "type", "resp", "mark", "comment")
    )
    df.to_csv(outf, index=False)


if __name__ == "__main__":
    main()
