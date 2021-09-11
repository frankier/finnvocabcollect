import sqlite3


QUERY = """
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
    derivation.type = "derivation"
ORDER BY
    derived_headword
"""


def get_wikiparse_derivs(wikiparse_db):
    cur = sqlite3.connect(wikiparse_db)
    derivs_grouped = {}
    res = cur.execute(QUERY)
    for deriv, deriv_id, part in res:
        derivs_grouped.setdefault((deriv, deriv_id), []).append(part.lstrip("-"))
    derivs = []
    for (deriv, deriv_id), segs in derivs_grouped.items():
        if deriv.startswith("-") or " " in deriv:
            continue
        yield deriv, deriv_id, [seg.rstrip("-") for seg in segs[:-1]], segs[-1]
