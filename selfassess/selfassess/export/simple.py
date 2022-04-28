import click
import duckdb


@click.command()
@click.argument("db_in")
@click.argument("tsv_out")
@click.option("--include-session/--no-include-session")
def main(db_in, tsv_out, include_session):
    conn = duckdb.connect(db_in)
    if include_session:
        session_col = "selfassess_response.session_id,\n"
    else:
        session_col = ""
    conn.execute(f"""
    copy (
        select
            participant.id as participant,
            {session_col}
            selfassess_response.word,
            selfassess_response.time_usecs,
            selfassess_response.rating,
            miniexam_mark.mark
        from
            selfassess_response
            join selfassess_session
                on selfassess_response.session_id = selfassess_session.id
            join participant
                on selfassess_session.participant_id = participant.id
            left outer join miniexam_response
                on participant.id = miniexam_response.participant_id
                and miniexam_response.word = selfassess_response.word
            left outer join miniexam_mark
                on miniexam_mark.miniexam_response_id = miniexam_response.id
        where
            miniexam_mark.marker = 'final'
            or miniexam_mark.marker is null
        order by
            participant,
            selfassess_response.rowid
    ) to '{tsv_out}' with ( header, delimiter '\t' );
    """)


if __name__ == "__main__":
    main()
