import sqlite3
import pandas
import click
from finnwordlist.utils.wordlists import read_nss
import orjson
from finntk import get_omorfi, analysis_to_subword_dicts
from finntk.omor.anlys import lemmas_of_subword_dicts
import re


DERIV_QUERY = """
SELECT
    der_head.name AS derived_headword,
    derivation.id AS derived_id,
    seg_head.name AS seg_headword
FROM
    headword AS der_head JOIN
    etymology ON etymology.headword_id = der_head.id LEFT OUTER JOIN
    derivation ON derivation.etymology_id = etymology.id LEFT OUTER JOIN
    derivation_seg ON derivation_seg.derivation_id = derivation.id LEFT OUTER JOIN
    headword AS seg_head ON derivation_seg.derived_seg_id = seg_head.id
WHERE
    derivation.type IN ("derivation", "compound")
ORDER BY
    LENGTH(derived_headword) DESC
"""


BAD_POS = {
    "name", "prefix", "suffix", "intj", "phrase", "prep_phrase", "proverb",
    "interfix", "affix", "infix", "symbol", "punct", "adv_phrase", "circumfix",
    "abbrev"
}


WORD_REGEX = re.compile(r"\b\w+")


def read_en(inf):
    words = set()
    for line in inf:
        word = orjson.loads(line)
        pos = word.get("pos")
        is_bad = pos in BAD_POS or " " in word["word"] or "-" in word["word"]
        if is_bad:
            continue
        words.add(word["word"].lower())
    return words


def read_fi_selfdef(inf):
    words = set()
    for line in inf:
        word = orjson.loads(line)
        pos = word.get("pos")
        is_bad = pos in BAD_POS or " " in word["word"] or "-" in word["word"]
        if is_bad:
            continue
        selfdef = any((
            word["word"] in WORD_REGEX.findall(gloss)
            for sense in word["senses"]
            for gloss in sense.get("glosses", ())
        ))
        if not selfdef:
            continue
        words.add(word["word"].lower())
    return words


@click.command()
@click.argument("wikiparse_db")
@click.argument("en_json", type=click.File("r"))
@click.argument("fi_json", type=click.File("r"))
@click.argument("outf")
def main(wikiparse_db, en_json, fi_json, outf):
    cur = sqlite3.connect(wikiparse_db)
    nss = read_nss(False)
    enwords = read_en(en_json)
    selfdef = read_fi_selfdef(fi_json)
    loans = enwords & selfdef
    derivs_grouped = {}
    res = cur.execute(DERIV_QUERY)
    for deriv, deriv_id, part in res:
        deriv_dict = derivs_grouped\
            .setdefault(deriv, {})
        if part is None:
            deriv_dict[deriv_id] = None
        else:
            deriv_dict.setdefault(deriv_id, [])\
                .append(part.strip("-"))
    all_loans = {}
    for word in sorted(nss, key=lambda word: len(word)):
        if word in loans:
            all_loans[word] = []
        elif word in derivs_grouped:
            all_have_loan = True
            non_loan_bits = []
            for ety_bits in derivs_grouped[word].values():
                found_loan = False
                if ety_bits is not None:
                    for part in ety_bits:
                        if len(part) > 3 and part in all_loans:
                            found_loan = True
                            non_loan_bits.extend(all_loans[part])
                        else:
                            non_loan_bits.append(part)
                if not found_loan:
                    all_have_loan = False
                    break
            if all_have_loan:
                all_loans[word] = non_loan_bits
    df = pandas.DataFrame({
        "words": list(all_loans.keys()),
        "non_loan_bits": list(all_loans.values()),
    })
    df.to_parquet(outf)


if __name__ == "__main__":
    main()
