import click
from gensim.models import KeyedVectors


@click.command()
@click.argument("inf")
@click.argument("outf")
def main(inf, outf):
    vectors = KeyedVectors.load_word2vec_format(inf, binary=False, no_header=True)
    vectors.save(outf)


if __name__ == "__main__":
    main()
