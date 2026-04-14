#!/usr/bin/env python3
"""
Convert pickled ETE3 trees into Newick + per-leaf state TSVs.

Expected input files (inside --folder):
  trees_<num_trees>/time_<time>/sample_<sample>/trial_<trial>/trees.pkl

Outputs (inside --folder/trees_<num_trees>/time_<time>/sample_<sample>/trial_<trial>/tree_nwks):
  tree_<i>.nw
  tree_<i>_states.tsv
  <num_trees>_trial_<trial>_locations.tsv

Example:
  python convert_sim_trees.py --folder /path/to/sims --num_trees 8 16 32 64 --num_trials 10
"""

from __future__ import annotations

import argparse
import pickle as pic
from pathlib import Path
from typing import Collection, Dict, List, Tuple

import pandas as pd
from ete3 import Tree 


def get_state_file(tree) -> pd.DataFrame:
    state_file: List[Tuple[str, object]] = []
    for node in tree.traverse("preorder"):
        if node.is_leaf():
            st = getattr(node, "state", None)
            state_file.append((node.name, st))
    return pd.DataFrame(state_file, columns=["cellBC", "cell_state"])


def assign_names_with_state(tree, leaf_prefix: str = "L", internal_prefix: str = "I"):
    name_map: Dict[str, str] = {}
    leaf_counter = 1
    internal_counter = 1

    for node in tree.traverse("preorder"):
        old_name = node.name or ""

        if node.is_leaf():
            base = f"{leaf_prefix}{leaf_counter}"
            leaf_counter += 1
        else:
            base = f"{internal_prefix}{internal_counter}"
            internal_counter += 1

        st = getattr(node, "state", None)
        new_name = f"{base}_{st}" if st is not None else base

        name_map[old_name] = new_name
        node.name = new_name

    return tree, name_map


def prune_leaves_by_state(tree, allowed_states: Collection, missing_policy: str = "drop"):
    allowed_states = set(allowed_states)

    total = len(tree)
    keep_names: List[str] = []
    missing_names: List[str] = []

    for leaf in tree.iter_leaves():
        st = getattr(leaf, "state", None)
        if st is None:
            if missing_policy == "error":
                raise ValueError(f"Leaf {leaf.name!r} has no `state` attribute.")
            elif missing_policy == "keep":
                keep_names.append(leaf.name)
            else:
                missing_names.append(leaf.name)
        elif st in allowed_states:
            keep_names.append(leaf.name)

    if keep_names:
        tree.prune(keep_names, preserve_branch_length=True)

    summary = {
        "total_leaves": total,
        "kept": len(keep_names),
        "pruned": total - len(keep_names),
        "pruned_missing_state": len(missing_names),
    }
    return tree, summary


def process_one_trial(
    input_dir: Path,
    allowed_states=('4', '5', '6', '7'),
    missing_policy: str = "drop"
):
    pkl_path = input_dir / "trees.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(f"Missing input pickle: {pkl_path}")

    out_dir = input_dir / "tree_nwks"
    out_dir.mkdir(parents=True, exist_ok=True)

    trees = pic.load(open(pkl_path, "rb"))
    if not isinstance(trees, list):
        raise TypeError(f"Expected list/tuple of trees in {pkl_path}, got {type(trees)}")

    locations: List[Tuple[str, str]] = []
    n = len(trees)

    for i in range(n):
        t = trees[i]
        assign_names_with_state(t)
        t, _ = prune_leaves_by_state(
            t,
            allowed_states=set(allowed_states),
            missing_policy=missing_policy,
        )

        states_path = out_dir / f"tree_{i}_states.tsv"
        newick_path = out_dir / f"tree_{i}.nw"

        get_state_file(t).to_csv(states_path, sep="\t", index=False)
        t.write(format=3, outfile=str(newick_path))

        locations.append((str(newick_path.resolve()), str(states_path.resolve())))

    loc_path = out_dir / f"locations.tsv"
    pd.DataFrame(locations).to_csv(loc_path, sep="\t", index=False, header=False)

    return {
        "input_pickle": str(pkl_path),
        "output_dir": str(out_dir),
        "n_written": n,
        "locations_file": str(loc_path),
    }


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, type=Path)
    ap.add_argument(
        "--num_trees",
        required=True,
        type=int,
        nargs="+",
    )
    ap.add_argument(
        "--samples",
        required=True,
        type=float,
        nargs="+",
    )
    ap.add_argument(
        "--num_trials",
        type=int,
        default=10,
        help="Number of trials (default=10 -> trials 0 to 9)",
    )
    ap.add_argument("--allowed_states", type=int, nargs="*", default=['4', '5', '6', '7'])
    ap.add_argument(
        "--missing_policy",
        choices=["drop", "keep", "error"],
        default="drop",
    )
    return ap.parse_args()


def main():
    args = parse_args()
    folder = args.folder.expanduser().resolve()

    if not folder.exists():
        raise FileNotFoundError(f"--folder does not exist: {folder}")

    for nt in args.num_trees:
        for sample in args.samples:
            for trial in range(args.num_trials):
                input_dir = folder / f"trees_{nt}" / "time_5.0" / f"sample_{sample}" / f"trial_{trial}"
                info = process_one_trial(
                    input_dir=input_dir,
                    allowed_states=args.allowed_states,
                    missing_policy=args.missing_policy
                )
                print(
                    f"wrote {info['n_written']} trees -> {info['output_dir']} "
                    f"(locations: {info['locations_file']})"
                )


if __name__ == "__main__":
    main()
