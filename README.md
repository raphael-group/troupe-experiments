## Simulation experiments for the TROUPE paper

This repository provides code to replicate the experiments in the paper "Inferring Cell Differentiation Dynamics with Unobserved Progenitors".
Note that it assumes access to a SLURM scheduled cluster.

First clone this repository and initialize the it using
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then clone TROUPE into a separate directory with
```
cd ..
git clone https://github.com/raphael-group/troupe.git
```

and `cd` into `troupe`, install as a package, then go back to the experiments directory
```
cd troupe
pip install -e .
cd ../troupe_experiments
```

To simulate trees, run the following command:
```
bash scripts/simulate_trees.sh
```

To get results for each method run the corresponding cluster script. For example, if you want to run TROUPE, you'd write
```
bash scripts/troupe/run_cluster_inference.sh
```
