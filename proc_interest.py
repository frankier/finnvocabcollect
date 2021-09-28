import click
import pandas
import langcodes
from nltk.tokenize import word_tokenize
import math


SHORT_COLS = [
    "ts",
    "email",
    "referer",
    "nativelang",
    "otherlang",
    "selfcefr",
    "howlong",
    "prooftype",
    "ykilevel",
    "ykiwhen",
    "ykispeaking",
    "ykilistening",
    "ykiwriting",
    "ykireading",
    "ykiotherinfo",
    "uniname",
    "unicoursename",
    "unigrade",
    "unicefr",
    "extrainfo",
    "otherproof"
]


LANG_FIXES = {
    "Mandiali": "Mandiali",
    "Veäjän kieli": "Venäjä",
}


def lang2code(lang):
    print(lang)
    try:
        lang = langcodes.find(lang)
        return lang.language
    except LookupError:
        # print("Fail", lang)
        return float("NaN")


def has_english(otherlang):
    if isinstance(otherlang, float) and math.isnan(otherlang):
        return False
    tokens = word_tokenize(otherlang)
    for idx in range(len(tokens)):
        joined = " ".join(tokens[idx:])
        try:
            lang = langcodes.find(joined)
            if lang.language == "en":
                return True
        except LookupError:
            pass
    return False


@click.command()
@click.argument("inf")
def main(inf):
    df = pandas.read_csv(inf)
    df.rename(columns=dict(zip(df.columns, SHORT_COLS)), inplace=True)
    df["selfcefr"] = df["selfcefr"].map(lambda cefr: cefr[:2])

    def drop(reason, criteron):
        print("Dropping {} rows because {}.".format(criteron.sum(), reason))
        print(df[criteron].index)
        df.drop(df[criteron].index, inplace=True)

    drop("<B1 CEFR", df["selfcefr"].isin(["A1", "A2"]))

    df["nativelang"] = df["nativelang"].map(lambda l: LANG_FIXES.get(l, l))
    df["nativelangcode"] = df["nativelang"].map(lang2code)
    drop("native language code lookup failed", df["nativelangcode"].isna())
    print(df)

    print(df.groupby(["nativelangcode"]).size().reset_index(name="counts"))
    print(df.groupby(["selfcefr"]).size().reset_index(name="counts"))
    print(
        df
        .groupby(["nativelangcode", "selfcefr"])
        .size()
        .reset_index(name="counts")
    )

    df["hasenglish"] = (
        (df["nativelangcode"] == "en") |
        (df["otherlang"].map(has_english))
    )
    print(df.groupby(["hasenglish"]).size().reset_index(name="counts"))
    print(df[~df["hasenglish"]])

    df_cand = df[
        df["nativelangcode"].isin(("en", "ru", "hu"))
        & df["selfcefr"].isin(["B1", "B2", "C1"])
    ]

    for name, group in df_cand.groupby(["nativelangcode", "selfcefr"]):
        print()
        print()
        print("** ", name, "**")
        for _, row in group.iterrows():
            print()
            for k, v in row.iteritems():
                print(k + ":")
                print("\t", v)


if __name__ == "__main__":
    main()
