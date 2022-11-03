from run_experiment import run_notebook, restore_notebook
from elastic.algorithm.selector import OptimizerType
import argparse

# Run scalability experiments on the generated DAGs.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook", help="Notebook to run experiment on")
    args = parser.parse_args()

    run_notebook(notebook=args.notebook)
    for optimizer_enum in OptimizerType:
        restore_notebook(notebook=args.notebook, optimizer=optimizer_enum.value)
