This project has two parts, the word list pipeline, which is
a [Snakemake](https://snakemake.readthedocs.io/en/stable/) project, and the
second is the self assessment website itself which is
a Quart (similar to Flask) project.

Instructions for the website, which has it's own set of
dependencies/pyproject.toml/Dockerfile are in `selfassess`.

The Snakemake project is backed by the Python module in `finnwordlist`. To
build the Snakemake project run:

    $ poetry install
    $ snakemake -j1 -C WIKIPARSE_DB=/path/to/wikiparse/defns.db

Where `WIKIPARSE_DB` is a parsed sqlite database from
[wikiparse](https://github.com/frankier/wikiparse).

Other things here:

 * `proc_interest.py`: Process the CSV of the ``expressions of interest`` CSV.
 * `plot_en_wordlist_freqs.py`: Plot a frequency histogram of the words in
   SVL12K and all English words known to wordfreq for comparison with the plots
   for the Finnish wordlist. You can run this with the Snakemake rule
   `plot_en_wordlist_freqs`.
