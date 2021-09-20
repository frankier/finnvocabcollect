import click
from .database import Word
from .utils import get_session


def create_db(session):
    from .database import Base
    Base.metadata.create_all(session.get_bind().engine)
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")


@click.command()
@click.argument("word_list", type=click.File("r"))
def main(word_list):
    session = get_session()
    create_db(session)
    for word in word_list.read().split("\n"):
        word = word.strip()
        if not word:
            continue
        session.add(Word(word=word))
    session.commit()


if __name__ == "__main__":
    main()
