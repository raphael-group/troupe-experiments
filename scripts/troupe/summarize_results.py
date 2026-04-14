import pickle
import numpy as np
import networkx as nx
import json
import os
import ete3
import csv

working_dir = "/n/fs/ragr-research/users/wh8114/projects/troupe_experiments"

import sys
sys.path.append(f'{working_dir}/scripts')

from eval_utils import (
    get_total_leaves,
    get_dict_l1_error,
    get_model,
    only_outgoing_edges,
    build_potency_model_from_params,
    get_reachable_idxs,
    get_jaccard_similarity_from_potency_kernels,
    dict_l1_norm
)

data_prefix="data/subsampled_leaves_4_terminals"
model_json_pth = f"{working_dir}/{data_prefix}/model.json"

with open(model_json_pth, 'r') as fp:
    data_dict = json.load(fp)
birth_kernel_true = np.array(data_dict["birth_kernel"])
growth_rate_true = np.array(data_dict["growth_rates"])
n = len(growth_rate_true)
terminals = [str(i) for i in range(n) if birth_kernel_true[i, i] == 1.0]
idx2potency = {}
for i in range(n):
    reachable_idxs = get_reachable_idxs(birth_kernel_true, i, 0.00001)
    potency_list = [str(j) for j in reachable_idxs if str(j) in terminals]
    potency_list.sort()
    potency = tuple(potency_list)
    idx2potency[i] = potency

# NOTE: Normalizing outgoing edges to sum to 1
# birth_kernel_true = only_outgoing_edges(birth_kernel_true)
potency_birth_kernel_true, potency_growth_rates_true = build_potency_model_from_params(birth_kernel_true, growth_rate_true, idx2potency)

terminal_set = set(terminals)

num_trees_list = [8, 16, 32, 64]
subsample_list = [0.05, 0.1, 0.2]
trials = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
rows = []
results_prefix="results/subsampled_leaves_4_terminals/troupe"

for num_trees in num_trees_list:
    print(num_trees)
    for subsample in subsample_list:
        print("\t", subsample)
        for trial in trials:
            tree_pth = (
                f"{working_dir}/{data_prefix}/trees_{num_trees}/time_5.0/"
                f"sample_{subsample}/trial_{trial}/trees.pkl"
            )
            best_model_pth = (
                f"{working_dir}/{results_prefix}/trees_{num_trees}/time_5.0/"
                f"sample_{subsample}/trial_{trial}/best_model_dict.pkl"
            )

            if not os.path.exists(tree_pth):
                print(f"Missing tree file: {tree_pth}")
                continue
            if not os.path.exists(best_model_pth):
                print(f"Missing model file: {best_model_pth}")
                continue

            num_leaves = get_total_leaves(tree_pth)

            birth_kernel, growth_rates, idx2potency, _ = get_model(best_model_pth)
            # NOTE: Normalizing outgoing edges to sum to 1
            # birth_kernel = only_outgoing_edges(birth_kernel)
            potency_birth_kernel, potency_growth_rates = build_potency_model_from_params(birth_kernel, growth_rates, idx2potency)

            birth_kernel_error = get_dict_l1_error(
                potency_birth_kernel, potency_birth_kernel_true
            )
            birth_kernel_rel_error = birth_kernel_error / (
                dict_l1_norm(potency_birth_kernel_true) + 1e-12
            )
            potency_jaccard_error = 1 - get_jaccard_similarity_from_potency_kernels(
                potency_birth_kernel, potency_birth_kernel_true
            )
            growth_rate_error = get_dict_l1_error(
                potency_growth_rates, potency_growth_rates_true
            )
            growth_rate_rel_error = growth_rate_error / (
                dict_l1_norm(potency_growth_rates_true) + 1e-12
            )

            rows.append({
                "num_trees": num_trees,
                "subsample": subsample,
                "trial": trial,
                "num_leaves": num_leaves,
                "birth_kernel_error": birth_kernel_error,
                "birth_kernel_rel_error": birth_kernel_rel_error,
                "jaccard_error": potency_jaccard_error,
                "growth_rate_error": growth_rate_error,
                "growth_rate_rel_error": growth_rate_rel_error,
                "method": "troupe"
            })

# Save summary table
out_csv = f"{working_dir}/{results_prefix}/parameter_comparison_summary.csv"
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

with open(out_csv, "w", newline="") as fp:
    writer = csv.DictWriter(fp, fieldnames=rows[0].keys() if rows else [])
    if rows:
        writer.writeheader()
        writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_csv}")