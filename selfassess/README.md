## Running locally

    $ poetry install
    $ . ./devenv.sh
    $ poetry run python -m selfassess.initdb wordlist.txt
    $ poetry run quart run

Every time you want to add a new participant run:

    $ poetry run python -m selfassess.new email@example.com

## List of commands

### Project maintenance

 * `quart` / `alembic` Run subcommands of quart (web framework) and alembic (db
   migrations)
 * `python -m selfassess.initdb wordlist.txt` Create a new database for a study
   based on `wordlist.txt`.


### Participant management

 * `python -m selfassess.new email@example.com`: Add a new participant
 * `python -m selfassess.action_participant`: Change status of participants by
    e.g. approving their responses of withdrawing them
 * `python -m selfassess.mark`: Mark a participant's answers
 * `python -m selfassess.status`: Get status of participants

# Data export

 * `python -m selfassess.export.duckdb` Export anonymised data to a DuckDB
   database
 * `python -m selfassess.export.csvs` Convert DuckDB database to CSVs
 * `python -m selfassess.export.simple` Convert DuckDB database to simple flat
   CSV with just information about the self assessment
 * `python -m selfassess.export.payment` Export participant information for
   payment
