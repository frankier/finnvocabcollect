import pandas
import click
from finnwordlist.utils.wordlists import read_nss
from finntk.omor.inst import get_omorfi
from finntk.omor.anlys import analysis_to_subword_dicts, generate_or_passthrough

DERIV_SUFFIXES = {
    "ja",
    "sti",
    "ton",
    "tön",
    "yys",
    "uus",
    "mpi",
    "in",
    "minen",
    "inen",
    "llinen",
    "nen",
    "mainen",
    "lainen"
}


def get_wikiparse_derivs(wikiparse_db):
    from finnwordlist.utils.deriv import get_wikiparse_derivs
    last = None
    for deriv, deriv_id, body_segs, suffix in get_wikiparse_derivs(wikiparse_db):
        if deriv == last:
            continue
        if suffix in DERIV_SUFFIXES:
            yield deriv, body_segs, suffix
            last = deriv


def get_omorfi_derivs(wordlist, got):
    omorfi = get_omorfi()
    for word in wordlist:
        if word in got:
            continue
        analyses = []
        for analysis in omorfi.analyse(word):
            subwords = list(analysis_to_subword_dicts(analysis.raw))
            if "drv" in subwords[-1]:
                analyses.append((subwords, subwords[-1]["drv"]))
        if len(analyses) == 0:
            continue
        subwords, drv = sorted(analyses, key=lambda tpl: len(tpl[0]))[0]
        head = "".join([
            *(next(iter(generate_or_passthrough(sw))) for sw in subwords[:-1]),
            subwords[-1]["word_id"]
        ])
        yield word, [head], drv


@click.command()
@click.argument("wikiparse_db")
@click.argument("outf")
def main(wikiparse_db, outf):
    nss = read_nss(False)
    wikiparse_derivs = get_wikiparse_derivs(wikiparse_db)
    derivs = []
    heads = []
    sufs = []
    for deriv, head, suf in wikiparse_derivs:
        derivs.append(deriv)
        heads.append(head)
        sufs.append(suf)
    for deriv, head, suf in get_omorfi_derivs(nss, derivs):
        derivs.append(deriv)
        heads.append(head)
        sufs.append(suf)
    df = pandas.DataFrame({
        "derivs": derivs,
        "heads": heads,
        "sufs": sufs
    })
    df.to_parquet(outf)


if __name__ == "__main__":
    main()
