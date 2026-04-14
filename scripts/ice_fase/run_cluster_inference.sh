
# for NUM_TREES in 8 16 32 64
#     for SAMPLE in 0.05 0.1 0.2
#         for TRIAL in 0 1 2 3 4 5 6 7 8 9

for NUM_TREES in 8 16 32 64
do
    for SAMPLE in 0.05 0.1 0.2
    do
        for TRIAL in 0 1 2 3 4 5 6 7 8 9
        do
            RESULTS_DIR=$PWD/results/subsampled_leaves_4_terminals/ice_fase/trees_$NUM_TREES/time_5.0/sample_$SAMPLE/trial_$TRIAL
            DATA_DIR=$PWD/data/subsampled_leaves_4_terminals/trees_$NUM_TREES/time_5.0/sample_$SAMPLE/trial_$TRIAL/tree_nwks/locations.tsv

            mkdir -p $RESULTS_DIR

            LOG_FILE=$RESULTS_DIR/run.log
            ERR_FILE=$RESULTS_DIR/run.err

            sbatch -o $LOG_FILE -e $ERR_FILE \
            /n/fs/ragr-research/users/wh8114/projects/troupe_experiments/scripts/ice_fase/run_single_inference.sh \
            $RESULTS_DIR \
            $DATA_DIR
        done
    done
done