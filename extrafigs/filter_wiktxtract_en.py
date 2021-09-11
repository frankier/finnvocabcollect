from collections import Counter
import click
import json
from more_itertools import unique_justseen


BAD_POS = {
    "name", "prefix", "suffix", "intj", "phrase", "prep_phrase", "proverb",
    "interfix", "affix", "infix", "symbol", "punct", "adv_phrase", "circumfix",
    "abbrev"
}


@click.command()
@click.argument("inf", type=click.File("r"))
@click.argument("outf", type=click.File("w"))
def main(inf, outf):
    counter = Counter()
    words = []
    for line in inf:
        word = json.loads(line)
        pos = word.get("pos")
        is_bad = pos in BAD_POS or " " in word["word"]
        if is_bad:
            continue
        counter[pos] += 1
        words.append(word["word"])
    for word in unique_justseen(sorted(words)):
        print(word, file=outf)
    for word, cnt in counter.most_common():
        print(word, cnt)


if __name__ == "__main__":
    main()
