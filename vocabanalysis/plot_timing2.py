import click
import matplotlib.pyplot as plt
from os import makedirs
from os.path import join as pjoin
import duckdb


def plot(usecs, rating, out_fn):
    fig, ax = plt.subplots()
    fig.set_size_inches(12, 12)
    ax.set_ylim(0, 20)
    ax.set_yticks(range(21))
    scatter = ax.scatter(x=range(len(usecs)), y=usecs, c=rating, label=rating)
    legend = ax.legend(
        *scatter.legend_elements(),
        title="Ratings"
    )
    ax.add_artist(legend)
    plt.tight_layout()
    fig.savefig(out_fn)
    plt.close(fig)


@click.command()
@click.argument("db_in")
@click.argument("pid", type=int)
@click.argument("figout")
def main(db_in, pid, figout):
    conn = duckdb.connect(db_in)
    df = conn.execute("""
    select
        selfassess_response.session_id as sid,
        selfassess_response.time_usecs as usecs,
        selfassess_response.rating as rating
    from
        selfassess_response
        join selfassess_session
        on selfassess_response.session_id = selfassess_session.id
    where
        selfassess_session.participant_id = ?
    """, (pid,)).fetchdf()
    makedirs(figout, exist_ok=True)
    for session_id, session_df in df.groupby("sid"):
        out_fn = pjoin(figout, f"{session_id}.png")
        plot(
            session_df["usecs"].astype(float) / 1000000,
            session_df["rating"],
            out_fn
        )


if __name__ == "__main__":
    main()
