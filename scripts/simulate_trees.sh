echo "Running script from root dir $PWD..."

for num_trees in 8
do
    for sample_prob in 0.05 0.1 0.2
    do    
        python $PWD/../troupe/scripts/simulate_data.py \
            -b 10 \
            -t 5.0 \
            -n $num_trees \
            -s $sample_prob \
            -r \
            -o $PWD/data/subsampled_leaves_4_terminals
    done
done