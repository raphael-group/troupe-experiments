#!/bin/bash
#SBATCH --job-name=ice_fase         # create a short name for your job
#SBATCH --nodes=1                   # node count
#SBATCH --ntasks=1                  # total number of tasks across all nodes
#SBATCH --cpus-per-task=1           # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem-per-cpu=8G            # memory per cpu-core (4G is default)
#SBATCH --time=00:10:00             # total run time limit (HH:MM:SS)

RESULTS_DIR=$1
DATA_DIR=$2

Rscript scripts/ice_fase/run_ice_fase.R \
                -p $RESULTS_DIR"/inferred" \
                -l $DATA_DIR