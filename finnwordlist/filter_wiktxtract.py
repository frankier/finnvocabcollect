import click
import json


BAD_CATEGORIES = [
    "Days of the week",
    "Months",
    "Languages",
    "Countries"
]


@click.command()
@click.argument("inf", type=click.File("r"))
@click.argument("outf", type=click.File("w"))
def main(inf, outf):
    words = set()
    for line in inf:
        word = json.loads(line)
        is_bad = (
            any(
                category in word.get("categories", ())
                for category in BAD_CATEGORIES
            )
            or any(
                category in sense.get("categories", ())
                for sense in word.get("senses", ())
                for category in BAD_CATEGORIES
            )
        )

        if not is_bad:
            continue
        words.add(word["word"].lower())
    for word in sorted(words):
        print(word, file=outf)


if __name__ == "__main__":
    main()
