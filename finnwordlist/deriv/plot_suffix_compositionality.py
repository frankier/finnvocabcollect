import seaborn
import pandas
from gensim.models import KeyedVectors
import sqlite3
import click
from finnwordlist.utils.deriv import get_wikiparse_derivs
from finnwordlist.compositionality import get_compositionality, MissingHead, MissingPart
from pprint import pprint
import matplotlib.pyplot as plt
from statistics import mean
import math


BLACKLIST = """
alue
sara
pallo
järjestelmä
tapa
kone
ryhmä
voima
paikka
aine
mies
raha
asema
työ
vuosi
kuva
sieni
""".strip().split("\n")


@click.command()
@click.argument("wikiparse_db")
@click.argument("vectors")
@click.argument("figout")
def main(wikiparse_db, vectors, figout):
    vectors = KeyedVectors.load(vectors)
    suffix_dists = {}
    for deriv, deriv_id, body_segs, suffix in get_wikiparse_derivs(wikiparse_db):
        if not body_segs:
            continue
        compos = get_compositionality(vectors, deriv, body_segs)
        if compos is MissingHead or compos is MissingPart:
            continue
        if math.isnan(compos):
            print(deriv, deriv_id, body_segs, suffix, vectors[deriv], [vectors[d] for d in body_segs])
        suffix_dists.setdefault(suffix, []).append(compos)
    fig = plt.figure()
    suffix_dists = {k: v for k, v in suffix_dists.items() if len(v) >= 30 and k not in BLACKLIST}
    seaborn.kdeplot(data=suffix_dists, common_norm=False)
    for compos, suffix in sorted(((mean(vals), suffix) for suffix, vals in suffix_dists.items())):
        print(suffix, compos)
    fig.savefig(figout)


if __name__ == "__main__":
    main()
