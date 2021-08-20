import click
from .database import Word
from .utils import get_session


@click.command()
@click.argument("word_list", type=click.File("r"))
def main(word_list):
    from .database import Base
    session = get_session()
    Base.metadata.create_all(session.get_bind().engine)
    for word in word_list.read().split("\n"):
        word = word.strip()
        if not word:
            continue
        session.add(Word(word=word))
    session.commit()


if __name__ == "__main__":
    main()
