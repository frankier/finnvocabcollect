This project has two parts, the word list pipeline, which is
a [Snakemake](https://snakemake.readthedocs.io/en/stable/) project, and the
second is the self assessment itself which is
a [Flask](https://flask.palletsprojects.com/en/2.0.x/)/[htmlx](https://htmx.org/)
project.

To build the Snakemake project run:

    $ poetry install
    $ snakemake -j1 -C WIKIPARSE_DB=/path/to/wikiparse/defns.db

Where `WIKIPARSE_DB` is a parsed sqlite database from
[wikiparse](https://github.com/frankier/wikiparse).
