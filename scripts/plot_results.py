#!/usr/bin/env python3


import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

"""
Example usage:

python scripts/plot_results.py 
    
"""

working_dir=f"/n/fs/ragr-research/users/wh8114/projects/troupe_experiments"
csv_paths=[
    f"{working_dir}/results/subsampled_leaves_4_terminals/troupe/parameter_comparison_summary.csv",
    f"{working_dir}/results/subsampled_leaves_4_terminals/ice_fase/parameter_comparison_summary.csv",
    f"{working_dir}/results/subsampled_leaves_4_terminals/classe/parameter_comparison_summary.csv",
]

outdir = f"{working_dir}/results/subsampled_leaves_4_terminals/figures"
os.makedirs(outdir, exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_binned_error_by_method(
    df: pd.DataFrame,
    outfile: str,
    num_leaves_col: str = "num_leaves",
    error_col: str = "birth_kernel_error",
    method_col: str = "method",
    n_bins: int = 10,
    figsize=(8, 5),
):
    """
    Partition num_leaves into percentile bins, then for each method:
      - compute average num_leaves in each bin
      - compute average error in each bin
      - plot average error vs average num_leaves as a line plot

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns [num_leaves_col, error_col, method_col].
    num_leaves_col : str
        Column containing number of leaves.
    error_col : str
        Column containing the error metric.
    method_col : str
        Column containing method names.
    n_bins : int
        Number of percentile bins.
    figsize : tuple
        Matplotlib figure size.

    Returns
    -------
    summary : pd.DataFrame
        Aggregated dataframe with one row per (method, bin).
    """

    required_cols = {num_leaves_col, error_col, method_col}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Keep only needed columns and drop missing values
    data = df[[num_leaves_col, error_col, method_col]].dropna().copy()

    if data.empty:
        raise ValueError("No valid rows remain after dropping missing values.")

    # Build percentile bins using UNIQUE num_leaves values so the binning
    # is not distorted by how many methods or replicates you have.
    unique_leaves = np.sort(data[num_leaves_col].unique())

    if len(unique_leaves) < 2:
        raise ValueError("Need at least two distinct num_leaves values to make bins.")

    # qcut on unique num_leaves values
    # duplicates='drop' handles cases where there are too few unique values
    leaf_bins = pd.qcut(
        unique_leaves,
        q=n_bins,
        labels=False,
        duplicates="drop",
    )

    leaf_to_bin = pd.DataFrame({
        num_leaves_col: unique_leaves,
        "leaf_bin": leaf_bins
    })

    data = data.merge(leaf_to_bin, on=num_leaves_col, how="left")

    # Aggregate within each method and bin
    summary = (
        data.groupby([method_col, "leaf_bin"], as_index=False)
        .agg(
            mean_num_leaves=(num_leaves_col, "mean"),
            mean_error=(error_col, "mean"),
            n_points=(error_col, "size"),
        )
        .sort_values([method_col, "mean_num_leaves"])
    )

    # Plot
    plt.figure(figsize=figsize)

    for method, group in summary.groupby(method_col):
        group = group.sort_values("mean_num_leaves")
        plt.plot(
            group["mean_num_leaves"],
            group["mean_error"],
            marker="o",
            label=str(method),
        )

    plt.xlabel("Average number of leaves")
    plt.xscale('log')
    plt.ylabel("Average error")
    plt.title(f"Average error by percentile bins of {num_leaves_col}")
    plt.legend(title=method_col)
    plt.tight_layout()
    plt.savefig(outfile)
    plt.clf()

    return summary


# Example usage:
# df should have columns: "num_leaves", "error", "method"
# summary_df = plot_binned_error_by_method(df, n_bins=10)
# print(summary_df)


def main():
    dfs = []
    for path in csv_paths:
        dfs.append(pd.read_csv(path, header=0))
    df = pd.concat(dfs, axis=0, ignore_index=True)
    
    x_key = 'num_trees'
    y_key = 'jaccard_error'
    sns.barplot(data=df, x=x_key, y=y_key, hue='method')
    file_name = f"{y_key}-by-{x_key}-barplot.pdf"
    plt.legend()
    plt.savefig(f"{outdir}/{file_name}")
    plt.clf()

    x_key = 'num_trees'
    y_key = 'birth_kernel_error'
    sns.barplot(data=df, x=x_key, y=y_key, hue='method')
    file_name = f"{y_key}-by-{x_key}-barplot.pdf"
    plt.legend()
    plt.savefig(f"{outdir}/{file_name}")
    plt.clf()

    x_key = 'num_trees'
    y_key = 'growth_rate_error'
    sns.barplot(data=df, x=x_key, y=y_key, hue='method')
    file_name = f"{y_key}-by-{x_key}-barplot.pdf"
    plt.legend()
    plt.savefig(f"{outdir}/{file_name}")
    plt.clf()


    x_key = 'num_leaves'           # 'num_trees', 'num_leaves'
    y_key = 'birth_kernel_error'  # 'birth_kernel_rel_error', 'growth_rate_error', 'growth_rate_rel_error' , 'birth_kernel_error',
    sns.scatterplot(data=df, x=x_key, y=y_key, alpha=0.75, hue='method')
    file_name = f"{y_key}-by-{x_key}-scatter.pdf"
    plt.legend()
    plt.xscale('log')
    os.makedirs(outdir, exist_ok=True)
    plt.savefig(f"{outdir}/{file_name}")

    plot_binned_error_by_method(df, f"{outdir}/error.pdf")


if __name__ == "__main__":
    main()