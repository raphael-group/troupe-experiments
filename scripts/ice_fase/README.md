To convert trees:

python scripts/ice_fase/convert_sim_trees.py \
--folder /n/fs/ragr-research/users/wh8114/projects/troupe_experiments/data/subsampled_leaves_4_terminals \
--num_trees 8 16 32 64 \
--samples 0.05 0.1 0.2 \
--num_trials 10




To run ice_fase:

NUM_TREES=8
SAMPLE=0.05
TRIAL=0
RESULTS_DIR=$PWD/results/subsampled_leaves_4_terminals/ice_fase/trees_$NUM_TREES/time_5.0/sample_$SAMPLE/trial_$TRIAL/inferred
DATA_DIR=$PWD/data/subsampled_leaves_4_terminals/trees_$NUM_TREES/time_5.0/sample_$SAMPLE/trial_$TRIAL/tree_nwks/locations.tsv

mkdir -p $RESULTS_DIR

Rscript scripts/ice_fase/run_ice_fase.R \
    -p $RESULTS_DIR \
    -l $DATA_DIR



To run carta:

python carta/carta.py --prefix test_outputs/test_carta \
    -k 4 \
    --file_locations /n/fs/ragr-research/users/ryz/new_org/inputs/16/trial_0/16_trial_0_locations.tsv \
    --states_file states.txt > test_outputs/test.std 2> test_outputs/test.err