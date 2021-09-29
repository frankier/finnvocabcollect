import click
import random
from .utils import get_session
from .database import ResponseSlot, Word, Participant
from sqlalchemy import func


def read_word_list(word_list):
    for word in word_list.read().split("\n"):
        word = word.strip()
        if not word:
            continue
        yield word


@click.command()
@click.argument("extra_words", type=click.File("r"))
def main(extra_words):
    session = get_session()
    word_list = list(read_word_list(extra_words))
    random.shuffle(word_list)
    current_words = session.query(func.count(Word.id)).scalar()
    word_rows = []
    for word in word_list:
        row = Word(word=word)
        session.add(row)
        word_rows.append(row)
    for participant in session.query(Participant):
        random.shuffle(word_rows)
        for response_order, word_row in enumerate(
            word_rows,
            start=current_words
        ):
            session.add(ResponseSlot(
                response_order=response_order,
                participant=participant,
                word=word_row
            ))
    session.commit()


if __name__ == "__main__":
    main()
