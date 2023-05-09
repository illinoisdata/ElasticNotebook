# ElasticNotebook

Welcome to ElasticNotebook! ElasticNotebook is a checkpoint/restore tool for Jupyter Notebook sessions, which uses a 
novel live migration mechanism that is reliable, efficient, and platform-independent.

## Getting Started

- Installing the package:
```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

- Try ElasticNotebook:

`elastic/examples` contains 5 example notebooks (`simple`, `numpy`, `pandas`, `pyspark`, `pytorch`). Simply click 'run
all' to run the notebook and create the checkpoint file for the session, then use the `restore_notebook` notebook to
restore the session.

## Running Experiments

Our experiment directory is `elastic/experiments`. The `elastic/experiments/notebooks` directory contains all 45
experiment notebooks which we evaluate on. 

The notebooks are hardcoded to read data from `/data/elastic-notebook/data/` (our NFS mount). To run experiments, download
the notebook data from Kaggle/JWST/Cornell Tutorials into subdirectories under `/data/elastic-notebook/data/`.

Shell scripts:
 - `run_notebook.sh`: run a specified notebook, and checkpoint/restore it using all evaluated methods (pickle, dumpsession, ElasticNotebook). Usage: `run_notebook.sh $notebook.ipynb`
 - `run_notebook_bandwidth.sh`: run the bandwidth experiments from Section 7.7.
 - `run_notebooks_jwst.sh`: run and checkpoint/restore all 5 JWST notebooks using all evaluated methods in order.
 - `run_notebooks_kaggle.sh`: Same as `run_notebooks_jwst.sh`, but with the 35 Kaggle notebooks.
 - `run_notebooks_overall.sh`: Same as `run_notebooks_jwst.sh`, but with the 10 notebooks reported in Sections 7.2 and 7.3.
 - `run_notebooks_scalability.sh`: Run the scalability experiments in Section 7.8.
 - `run_notebooks_tutorial.sh`: Same as `run_notebooks_jwst.sh`, but with the 5 Cornell Tutorial notebooks.

## Project Structure

```
elastic-notebook
│   ElasticNotebook.py                     ## top-level cell magic
│───algorithm
│   │───baseline.py                        ##  Migrate/recompute all baselines
│   │───optimizer_exact.py                 ##  Replication plan generation via min-cut reduction (Section 5.3)
│   └───selector.py                        ##  Optimizer base class
│───core
│   │───common
│   │   │───checkpoint_file.py             ## Struct of ElasticNotebook's checkpoint file
│   │   │───profile_graph_size.py          ## Size estimator for ElasticNotebook's Application History Graph
│   │   │───profile_migration_speed.py     ## Profiler for network bandwidth
│   │   └───profile_variable_size.py       ## Profiler for variable size
│   │───graph
│   │   │───cell_execution.py              ## Data structure for Cell Executions
│   │   │───graph.py                       ## ElasticNotebook's Application History Graph (Section 4.1)
│   │   └───variable_snapshot.py           ## Data strcutre for Variable Snapshots
│   │───io
│   │   │───adapter.py                     ## File writer base class
│   │   │───filesystem_adapter.py          ## Writer for writing checkpoint file to NFS
│   │   │───migrate.py                     ## Helper for creating checkpoint file
│   │   │───pickle.py                      ## Helper for variable serializability detection
│   │   └───recover.py                     ## Helper for unpacking checkpoint file
│   │───mutation
│   │   │───fingerprint.py                 ## Helper for detecting variable modifications via ID graph and object hash
│   │   │───id_graph.py                    ## ID graph construction and comparison (Section 4.2)
│   │   └───object_hash.py                 ## Object hash construction and comparison (Section 4.2)
│   └───notebook
│       │───checkpoint.py                  ## Line magic for checkpointing notebook session (Section 3.2)
│       │───find_input_vars.py             ## AST analysis module for finding input variables
│       │───find_output_vars.py            ## Helper for finding created/deleted variables via namespace difference
│       │───restore_notebook.py            ## Line magic for restoring notebook session (Section 3.2)
│       └───update_graph.py                ## Helper for updating Application History Graph
│───examples                               ## Example notebooks
│   └...
│───experiment                             ## Experiment scripts and notebooks (described above)
│   └...
└───test                                   ## Test modules
    └...
```
