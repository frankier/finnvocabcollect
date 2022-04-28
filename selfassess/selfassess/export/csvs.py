import click
import duckdb
import os


@click.command()
@click.argument("db_in")
@click.argument("csvs_out")
def main(db_in, csvs_out):
    conn = duckdb.connect(db_in)
    os.makedirs(csvs_out, exist_ok=True)

    conn.execute(f"""
    EXPORT DATABASE '{csvs_out}' (FORMAT CSV, DELIMITER '\t', HEADER TRUE);
    """)


if __name__ == "__main__":
    main()
