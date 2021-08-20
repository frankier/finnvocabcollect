## Running locally

    $ poetry install
    $ . ./devenv.sh
    $ poetry run python -m selfassess.initdb wordlist.txt
    $ poetry run quart run

Every time you want to add a new participant run:

    $ poetry run python -m selfassess.new email@example.com
