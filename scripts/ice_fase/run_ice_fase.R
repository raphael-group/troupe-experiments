#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ape)
  library(qfm)
  library(optparse)
  library(phangorn)
})

`%||%` <- function(a, b) if (!is.null(a)) a else b

##########Helper Functions###########

# If the root (node nTips+1) has exactly 1 child, remove that edge and
# add its length into root.edge, renumbering internal nodes appropriately.
fix_unary_root_keep_time <- function(tr) {
  nTips <- length(tr$tip.label)
  root  <- nTips + 1

  outdeg <- tabulate(tr$edge[, 1], nbins = nTips + tr$Nnode)
  if (outdeg[root] != 1) return(tr)

  idx <- which(tr$edge[, 1] == root)
  if (length(idx) != 1) {
    stop("Root outdegree says 1 but found !=1 root->child edges; tree may be malformed.")
  }

  addlen <- 0
  if (!is.null(tr$edge.length)) addlen <- tr$edge.length[idx]

  tr$edge <- tr$edge[-idx, , drop = FALSE]
  if (!is.null(tr$edge.length)) tr$edge.length <- tr$edge.length[-idx]

  tr$root.edge <- (tr$root.edge %||% 0) + addlen

  tr$edge[tr$edge > root] <- tr$edge[tr$edge > root] - 1
  tr$Nnode <- tr$Nnode - 1

  if (!is.null(tr$node.label)) {
    if (length(tr$node.label) == (tr$Nnode + 1)) {
      tr$node.label <- tr$node.label[-1]
    }
    if (length(tr$node.label) != tr$Nnode) {
      tr$node.label <- paste0("Node", seq_len(tr$Nnode))
    }
  } else {
    tr$node.label <- paste0("Node", seq_len(tr$Nnode))
  }

  tr
}

align_tree_and_meta <- function(tr, meta_vec) {
  if (!identical(tr$tip.label, names(meta_vec))) {
    cat("Tree tips:\n"); print(tr$tip.label)
    cat("Metadata names:\n"); print(names(meta_vec))
    stop("Tree tip labels and metadata names are not identical (including order).")
  }
  list(tr = tr, meta = meta_vec)
}

# Merge trees under a dummy root. Keep everything binary by adding a 0-length ladder.
# IMPORTANT: push each subtree's root.edge into the connector edge length (dummy->subroot).
merge_trees_under_dummy_root <- function(trees) {
  k <- length(trees)
  if (k == 0) stop("No trees to merge.")
  if (k == 1) {
    # If there's only one tree, it already has its own root.edge semantics.
    return(trees[[1]])
  }

  n_tips_each  <- vapply(trees, function(tr) as.integer(length(tr$tip.label)), integer(1))
  n_nodes_each <- vapply(trees, function(tr) as.integer(tr$Nnode), integer(1))
  rootedge_each <- vapply(trees, function(tr) tr$root.edge %||% 0, numeric(1))

  N <- sum(n_tips_each)
  tip_labels <- unlist(lapply(trees, `[[`, "tip.label"), use.names = FALSE)

  # allocate node IDs so dummy root is N+1 (ape convention)
  root_id <- N + 1
  internal_cursor <- N + 2

  internal_start <- integer(k)
  for (i in seq_len(k)) {
    internal_start[i] <- internal_cursor
    internal_cursor <- internal_cursor + n_nodes_each[i]
  }

  # ladder nodes needed if k > 2
  extra_needed <- max(0L, k - 2L)
  ladder_nodes <- if (extra_needed > 0) seq(internal_cursor, length.out = extra_needed) else integer(0)

  edges_all <- matrix(numeric(0), ncol = 2)
  lens_all  <- numeric(0)

  tip_cursor <- 0L
  subtree_root_ids <- integer(k)

  for (i in seq_len(k)) {
    tr <- trees[[i]]
    n_old <- length(tr$tip.label)
    nnode_old <- tr$Nnode

    # map old tips -> new tips
    new_tips <- (tip_cursor + 1L):(tip_cursor + n_old)
    tip_cursor <- tip_cursor + n_old

    # map old internals -> new internals
    new_internals <- internal_start[i] + (0:(nnode_old - 1L))

    map <- integer(n_old + nnode_old)
    map[1:n_old] <- new_tips
    map[(n_old + 1L):(n_old + nnode_old)] <- new_internals

    # old root is (n_old + 1)
    subtree_root_ids[i] <- map[n_old + 1L]

    e <- tr$edge
    e_mapped <- cbind(map[e[, 1]], map[e[, 2]])
    edges_all <- rbind(edges_all, e_mapped)

    el <- tr$edge.length %||% rep(0, nrow(tr$edge))
    lens_all <- c(lens_all, el)
  }

  # Build binary ladder at the top, with connector lengths:
  # dummy->subroot_i has length = rootedge_each[i]
  # ladder edges have length 0
  edges_top <- matrix(numeric(0), ncol = 2)
  lens_top  <- numeric(0)

  if (k == 2) {
    edges_top <- rbind(
      c(root_id, subtree_root_ids[1]),
      c(root_id, subtree_root_ids[2])
    )
    lens_top <- c(rootedge_each[1], rootedge_each[2])
  } else {
    current_parent <- root_id

    for (i in 1:(k - 2)) {
      next_internal <- ladder_nodes[i]

      # current_parent -> subtree i  (length = rootedge_i)
      edges_top <- rbind(edges_top, c(current_parent, subtree_root_ids[i]))
      lens_top  <- c(lens_top, rootedge_each[i])

      # current_parent -> next ladder node (length = 0)
      edges_top <- rbind(edges_top, c(current_parent, next_internal))
      lens_top  <- c(lens_top, 0)

      current_parent <- next_internal
    }

    # final two subtrees off the last ladder node
    edges_top <- rbind(edges_top, c(current_parent, subtree_root_ids[k - 1]))
    lens_top  <- c(lens_top, rootedge_each[k - 1])

    edges_top <- rbind(edges_top, c(current_parent, subtree_root_ids[k]))
    lens_top  <- c(lens_top, rootedge_each[k])
  }

  edges_all <- rbind(edges_all, edges_top)
  lens_all  <- c(lens_all, lens_top)

  merged <- list(
    edge = edges_all,
    edge.length = lens_all,
    tip.label = tip_labels,
    Nnode = sum(n_nodes_each) + (k - 1L),   # dummy root + (k-2) ladder nodes = (k-1)
    node.label = paste0("Node", seq_len(sum(n_nodes_each) + (k - 1L))),
    root.edge = NULL                         # single dummy root; we’ve pushed subtree root.edge into connectors
  )
  class(merged) <- "phylo"

  merged <- reorder.phylo(merged, order = "cladewise")
  merged
}

potency_edge_df <- function(tree, out,
                            node_col = "progenitor_state",
                            d1 = "downstream_state1", w1 = "downstream_size1", nb1 = "commitment_bias1",
                            d2 = "downstream_state2", w2 = "downstream_size2", nb2 = "commitment_bias2") {
  stopifnot(inherits(tree, "phylo"))
  stopifnot(all(c(node_col, d1, w1, nb1, d2, w2, nb2) %in% names(out)))

  # Ensure internal node names exist
  if (is.null(tree$node.label)) tree$node.label <- rep("", tree$Nnode)
  if (any(tree$node.label == "")) {
    miss <- which(tree$node.label == "")
    tree$node.label[miss] <- paste0("Node-", miss)
  }

  # internal node name -> phylo node index (tip indices are 1..Ntip, internal are Ntip+1..Ntip+Nnode)
  internal_idx <- function(nm) {
    i <- match(nm, tree$node.label)
    if (is.na(i)) return(NA_integer_)
    Ntip(tree) + i
  }

  # "state" string -> potency set (leaf labels)
  # - if it's an internal node label: all descendant tips
  # - else if it's a tip label: singleton
  state_to_potency <- function(state) {
    state <- as.character(state)
    if (is.na(state) || state == "") return(NA)

    ii <- internal_idx(state)
    if (!is.na(ii)) {
      tips <- Descendants(tree, ii, type = "tips")[[1]]
      return(sort(tree$tip.label[tips]))
    }

    # treat as tip label (cell type)
    if (state %in% tree$tip.label) return(state)

    stop("State '", state, "' not found in tree$node.label or tree$tip.label.")
  }

  # Build rows (only for edges that exist in out)
  src_states <- as.character(out[[node_col]])
  src_pots <- lapply(src_states, state_to_potency)

  make_rows <- function(dst_col, wt_col, nb_col) {
    dst_states <- out[[dst_col]]
    keep <- !(is.na(dst_states) | dst_states == "")

    data.frame(
      src_state = src_states[keep],
      dst_state = as.character(dst_states[keep]),
      edge_weight = as.numeric(out[[wt_col]][keep]),
      normalized_edge_weight = as.numeric(out[[nb_col]][keep]),
      stringsAsFactors = FALSE
    ) |>
      within({
        src_potency  <- src_pots[keep]
        sink_potency <- lapply(dst_state, state_to_potency)
      })
  }

  edges1 <- make_rows(d1, w1, nb1)
  edges2 <- make_rows(d2, w2, nb2)

  edges <- rbind(edges1, edges2)

  # Keep only requested columns (potency sets + weights). Potencies are list-cols of character vectors.
  edges <- edges[, c("src_potency", "sink_potency", "edge_weight", "normalized_edge_weight")]

  edges
}

write_unique_potencies <- function(edges_df, file) {

  # Combine source + sink potencies
  all_pots <- c(edges_df$src_potency, edges_df$sink_potency)

  # Canonicalize (sorted, unique)
  canon <- lapply(all_pots, function(x) sort(unique(as.character(x))))

  # ---- DROP SINGLETONS ----
  canon <- canon[vapply(canon, length, integer(1)) > 1]

  if (length(canon) == 0) {
    writeLines(character(0), file)
    return(invisible(NULL))
  }

  # Deduplicate sets (order-invariant)
  keys <- vapply(canon, paste, collapse = "|", FUN.VALUE = character(1))
  uniq <- canon[!duplicated(keys)]

  # Format: {'4', '5'}
  fmt <- vapply(
    uniq,
    function(x) paste0("{'", paste(x, collapse = "', '"), "'}"),
    FUN.VALUE = character(1)
  )

  writeLines(fmt, con = file)

  invisible(fmt)
}


edges_df_to_strings <- function(edges_df) {
  df <- edges_df
  df$src_potency <- vapply(df$src_potency,  \(x) paste0("{'", paste(x, collapse="', '"), "'}"), character(1))
  df$sink_potency <- vapply(df$sink_potency, \(x) paste0("{'", paste(x, collapse="', '"), "'}"), character(1))
  df
}

##########End of Helper Functions###########


option_list <- list(
  make_option(c("-p", "--prefix"), type = "character",
              help = "The prefix where to store the output."),
  make_option(c("-l", "--file_locations"), type = "character",
              help = "File with tab-separated: <tree_path> <meta_path> per line.")
)
opt <- parse_args(OptionParser(option_list = option_list))

trees_kept <- list()
metas_kept <- list()

con <- file(opt$file_locations, "r")
i_line <- 0L
while (TRUE) {
  line <- readLines(con, n = 1)
  if (length(line) == 0) break
  i_line <- i_line + 1L

  files <- strsplit(line, split = "\t")[[1]]
  tr <- read.tree(files[1])

  # Skip trees with <= 1 tip
  if (length(tr$tip.label) <= 1) {
    cat("Skipping tree with", length(tr$tip.label), "tip(s):", files[1], "\n")
    next
  }

  meta <- read.table(files[2], sep = "\t", header = TRUE)
  meta_vec <- unlist(as.character(meta[["cell_state"]]))
  names(meta_vec) <- meta$cellBC

  # Make tips globally unique if needed
  existing_tips <- unlist(lapply(trees_kept, `[[`, "tip.label"), use.names = FALSE)
  if (any(tr$tip.label %in% existing_tips)) {
    prefix <- paste0("T", i_line, "_")
    tr$tip.label <- paste0(prefix, tr$tip.label)
    names(meta_vec) <- paste0(prefix, names(meta_vec))
  }

  # Fix unary root by folding root->child time into root.edge
  tr <- fix_unary_root_keep_time(tr)

  aligned <- align_tree_and_meta(tr, meta_vec)

  # # Drop trees with only 1 cell type
  # if (length(unique(aligned$meta)) <= 1) {
  #   cat("Skipping tree (all tips same cell_state):", files[1], "\n")
  #   next
  # }

  # Ensure each subtree is binary
  if (!is.binary(aligned$tr)) {
    aligned$tr <- multi2di(aligned$tr, random = TRUE)
  }

  trees_kept[[length(trees_kept) + 1]] <- aligned$tr
  metas_kept[[length(metas_kept) + 1]] <- aligned$meta
}
close(con)

if (length(trees_kept) == 0) stop("No trees left after filtering; nothing to run.")

# Merge under dummy root, pushing each subtree's root.edge into the connector edge
tr_merged <- merge_trees_under_dummy_root(trees_kept)

rt <- node.depth.edgelength(tr_merged)[seq_along(tr_merged$tip.label)]
names(rt) <- tr_merged$tip.label

# Concatenate cell types (must align with merged tips)
sc_celltypes <- unlist(metas_kept, use.names = FALSE)
names(sc_celltypes) <- tr_merged$tip.label

if (!identical(names(sc_celltypes), tr_merged$tip.label)) {
  stop("Internal error: merged tip labels and sc_celltypes names are misaligned.")
}

res <- ice_fase(tr_merged, sc_celltypes, total_time = 2.35, root_time = 0.001)
# print(ls.str(res))
write.table(output_estimates(res), file = paste0(opt$prefix, "_output_estimates.txt"), append = FALSE)
out <- output_estimates(res)
write.tree(res$gr, file = paste0(opt$prefix, "_IceFaseGraph.nwk"), append = FALSE)

edges_df <- potency_edge_df(res$gr, out)
edges_df_str <- edges_df_to_strings(edges_df)

write.table(
  edges_df_str,
  file = paste0(opt$prefix, "_edge_weights.txt"),
  sep = "\t", row.names = FALSE, quote = FALSE
)
write_unique_potencies(edges_df, paste0(opt$prefix, "_progenitors.txt"))