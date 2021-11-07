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
            selfassess_response.rating
        from
            selfassess_response
            join selfassess_session
            on selfassess_response.session_id = selfassess_session.id
            join participant
            on selfassess_session.participant_id = participant.id
    ) to '{tsv_out}' with ( header );
    """)


if __name__ == "__main__":
    main()
