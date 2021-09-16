import click
import duckdb
import os


@click.command()
@click.argument("db_in")
@click.argument("tsv_out")
def main(db_in, tsv_out):
    conn = duckdb.connect(db_in)
    conn.execute(f"""
    copy (
        select
            participant.id as participant,
            selfassess_response.word,
            selfassess_response.time_secs,
            selfassess_response.grade
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
