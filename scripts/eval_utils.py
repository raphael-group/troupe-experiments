import pickle
import numpy as np
import networkx as nx
import json
import os
import ete3
import csv

def get_total_leaves(tree_pth):
    with open(tree_pth, "rb") as fp:
        tree_list = pickle.load(fp)
    return sum(len(tree.get_leaves()) for tree in tree_list)

def get_model(model_pth):
    with open(model_pth, "rb") as fp:
        model_dict = pickle.load(fp)

    birth_kernel = np.asarray(model_dict["daughter_kernel"], dtype=float)
    growth_rates = np.asarray(model_dict["growth_rates"], dtype=float)
    if "idx2potency" in model_dict:
        idx2potency = model_dict["idx2potency"] # NOTE: May need to do special handling for potencys?
    else:
        idx2potency = None

    if "idx2state" in model_dict:
        idx2state = model_dict["idx2state"] # NOTE: May need to do special handling for potencys?
    else:
        idx2potency = None

    return birth_kernel, growth_rates, idx2potency, idx2state

def only_outgoing_edges(birth_kernel):
    """Given a birth kernel, sets all self edges to 0 and normalizes outgoing edges
    for non-terminal rows."""
    adj_mat = np.copy(birth_kernel)
    for i in range(len(birth_kernel)):
        adj_mat[i,i] = 0
        row_sum = np.sum(adj_mat[i, :])
        if row_sum > 0:
            adj_mat[i:] /= row_sum
    return adj_mat

def build_potency_model_from_params(birth_kernel, growth_rates, idx2potency):
    num_states = len(idx2potency)
    non_zero_idxs = [(i,j) for i in range(num_states) for j in range(num_states) if birth_kernel[i,j] > 0]
    potency_birth_kernel = {(idx2potency[i], idx2potency[j]): float(birth_kernel[i,j]) for i,j in non_zero_idxs}
    potency_growth_rates = {idx2potency[i]: float(growth_rates[i]) for i in range(num_states)}
    return potency_birth_kernel, potency_growth_rates

def get_reachable_idxs(adj_matrix, starting_state, threshold):
    G = nx.DiGraph()
    num_nodes = len(adj_matrix)
    for i in range(num_nodes):
        for j in range(num_nodes):
            weight = adj_matrix[i, j]
            if weight > threshold:
                G.add_edge(i, j, weight=weight)

    assert starting_state in G

    reachable_nodes = list(nx.descendants(G, starting_state))
    reachable_nodes.append(starting_state)
    return reachable_nodes

def get_dict_l1_error(d1, d2):
    keys = set(d1.keys()) | set(d2.keys())
    return sum(abs(float(d1.get(k, 0.0)) - float(d2.get(k, 0.0))) for k in keys)

def get_jaccard_similarity_from_potency_kernels(d1, d2, remove_terminal_potency=True):
    d1_potencies = {edge[0] for edge, w in d1.items() if len(edge[0]) > 1}
    d2_potencies = {edge[0] for edge, w in d2.items() if len(edge[0]) > 1}
    intersection = d1_potencies.intersection(d2_potencies)
    union = d1_potencies.union(d2_potencies)
    return len(intersection) / len(union)


def dict_l1_norm(d):
    return sum(abs(float(v)) for v in d.values())