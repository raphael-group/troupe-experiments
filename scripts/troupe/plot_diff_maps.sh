
TROUPE_DIR_PATH=../troupe

for num_trees in 16 32 64
do
    echo "num trees=$num_trees"
    for sample_prob in 0.05 0.1 0.2
    do
        for trial in 0 1 2 3 4 5 6 7 8 9
        do

            python $TROUPE_DIR_PATH/scripts/evaluate_results.py plot-differentiation-maps \
                -i $PWD/results/subsampled_leaves_4_terminals/troupe/trees_$num_trees/time_5.0/sample_$sample_prob/trial_$trial

        done
    done
done