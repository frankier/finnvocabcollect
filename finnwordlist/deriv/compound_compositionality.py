import pandas
from gensim.models import KeyedVectors
from scipy.spatial import distance
from numpy.linalg import norm
import sqlite3
import click


MissingHead = object()
MissingPart = object()


QUERY = """
SELECT
    der_head.name AS derived_headword,
    seg_head.name AS seg_headword
FROM
    headword AS der_head JOIN
    etymology ON etymology.headword_id = der_head.id LEFT OUTER JOIN
    derivation ON derivation.etymology_id = etymology.id LEFT OUTER JOIN
    derivation_seg ON derivation_seg.derivation_id = derivation.id LEFT OUTER JOIN
    headword AS seg_head ON derivation_seg.derived_seg_id = seg_head.id
WHERE
    derivation.type = "compound"
ORDER BY
    derived_headword
"""


def get_compositionality(vectors, compound, parts):
    try:
        compound_vec = vectors[compound]
    except KeyError:
        return MissingHead
    try:
        composed_vec = sum((vectors[part] / norm(vectors[part]) for part in parts))
    except KeyError:
        return MissingPart
    return 1 - distance.cosine(compound_vec, composed_vec)


@click.command()
@click.argument("wikiparse_db")
@click.argument("vectors")
@click.argument("outf")
def main(wikiparse_db, vectors, outf):
    cur = sqlite3.connect(wikiparse_db)
    vectors = KeyedVectors.load(vectors)
    compounds_grouped = {}
    res = cur.execute(QUERY)
    for compound, part in res:
        compounds_grouped.setdefault(compound, set()).add(part)
    compounds = []
    all_parts = []
    compositionalities = []
    for compound, parts in compounds_grouped.items():
        compos = get_compositionality(vectors, compound, parts)
        if compos is MissingHead or compos is MissingPart:
            continue
        compounds.append(compound)
        all_parts.append(list(parts))
        compositionalities.append(compos)
    df = pandas.DataFrame({
        "compound": compounds,
        "parts": all_parts,
        "compositionality": compositionalities
    })
    df.to_parquet(outf)


if __name__ == "__main__":
    main()
