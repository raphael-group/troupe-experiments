To convert trees:

python convert_sim_trees.py --folder /n/fs/ragr-research/users/ryz/new_org/inputs --num_trees 16



To run ice_fase:

Rscript ice_fase/run_ice_fase.R \
    -p test_outputs/test \
    -l /n/fs/ragr-research/users/ryz/new_org/inputs/16/trial_0/16_trial_0_locations.tsv



To run carta:

python carta/carta.py --prefix test_outputs/test_carta \
    -k 4 \
    --file_locations /n/fs/ragr-research/users/ryz/new_org/inputs/16/trial_0/16_trial_0_locations.tsv \
    --states_file states.txt > test_outputs/test.std 2> test_outputs/test.err