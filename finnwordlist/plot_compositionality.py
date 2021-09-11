import click
import seaborn
import matplotlib.pyplot as plt
import pandas
import numpy as np
import scipy.stats as stats


def kde_mode(kernel, values):
    height = kernel.pdf(values)
    return values[np.argmax(height)]


@click.command()
@click.argument("df")
@click.argument("figout")
def main(df, figout):
    df = pandas.read_parquet(df)
    fig = plt.figure()
    compositionalities = df["compositionality"]
    seaborn.histplot(compositionalities, kde=True)
    kernel = stats.gaussian_kde(compositionalities)
    print("Mode:", kde_mode(kernel, compositionalities))
    samples = kernel.resample(size=10000)[0]
    print("Density > 0.9:", (samples > 0.9).sum() / len(samples))
    print("Point where integral reaches 0.2", np.sort(samples)[int(0.2 * len(samples))])
    fig.savefig(figout)


if __name__ == "__main__":
    main()
