import pickle
import numpy as np
import networkx as nx
import json
import os
import ete3
import csv
from itertools import combinations, permutations

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


### TODO: Wrap this in a function call
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
### return potency_birth_kernel_true, potency_growth_rates_true, terminal_set

def isomorphic_error(mat1, mat2, obs_states=None):
    """
    Return minimum achievable error between numpy matrices mat1 and mat2 among all
    row/col permutations. Assumes that obs_states are the first indices in the array
    """
    assert mat1.shape == mat2.shape
    num_states = len(mat1)
    idxs = set(range(num_states))
    if obs_states is None:
        num_observed = 0
        unobserved_states = idxs
    else:
        num_observed = len(obs_states)
        unobserved_states = idxs.difference(set(obs_states))
    num_unobserved = num_states - num_observed
    assert num_unobserved == len(unobserved_states)
    min_err = 1e20
    min_perm = None
    for perm in permutations(list(unobserved_states)):
        perm_list = list(perm)
        if obs_states is not None:
            perm_list += obs_states
        labels = np.array(perm_list)
        # Swap rows
        remixed = mat1[labels]
        # Then the cols
        remixed = remixed.T[labels].T
        err = np.sum(np.abs(remixed - mat2))
        if err < min_err:
            min_perm = labels
            min_err = err
    return min_err, min_perm

num_trees_list = [8, 16, 32, 64]
subsample_list = [0.05, 0.1, 0.2]
trials = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
rows = []
results_prefix="results/subsampled_leaves_4_terminals/classe"

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
                f"sample_{subsample}/trial_{trial}/hidden=4/model_dict.pkl"
            )

            if not os.path.exists(tree_pth):
                print(f"Missing tree file: {tree_pth}")
                continue
            if not os.path.exists(best_model_pth):
                print(f"Missing model file: {best_model_pth}")
                continue

            num_leaves = get_total_leaves(tree_pth)

            birth_kernel, growth_rates, _, idx2state = get_model(best_model_pth)
            # NOTE: Normalizing outgoing edges to sum to 1
            # birth_kernel = only_outgoing_edges(birth_kernel)

            idx2potency = {}
            for i in range(n):
                reachable_idxs = get_reachable_idxs(birth_kernel, i, 0.05)
                potency_list = [idx2state[j] for j in reachable_idxs if idx2state[j] in terminals]
                # if len(potency_list) <= 1:
                #     continue
                potency_list.sort()
                potency = tuple(potency_list)
                idx2potency[i] = potency

            potencies = {pot for pot in idx2potency.values() if len(pot) > 1}
            # print(idx2potency)
            print("Inferred:", potencies)
            # print("True")
            # print({edge[0] for edge, w in potency_birth_kernel_true.items() if len(edge[0]) > 1})
            if len(idx2potency) == len(potencies):   # Model has unique potencies
                print("\t Model has unique potencies!")
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
            else:
                l1_true = dict_l1_norm(potency_birth_kernel_true) + 1e-12
                growth_l1_true = dict_l1_norm(potency_growth_rates_true) + 1e-12
                birth_kernel_error, perm = isomorphic_error(birth_kernel, birth_kernel_true)
                birth_kernel_rel_error = birth_kernel_error / l1_true
                potency_edges = {(p, None): -1 for p in potencies if len(p) > 1}
                potency_jaccard_error =  1 - get_jaccard_similarity_from_potency_kernels(
                    potency_edges, potency_birth_kernel_true
                )
                growth_rate_error = np.sum(np.abs(growth_rates[perm] - growth_rate_true))
                growth_rate_rel_error = growth_rate_error / growth_l1_true

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
                "method": "classe"
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