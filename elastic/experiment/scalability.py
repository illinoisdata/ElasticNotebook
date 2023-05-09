from utils import run_notebook_scale
import argparse

# Python script for running and checkpointing a notebook.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook", help="Notebook to run experiment on")
    args = parser.parse_args()

    # Run the notebook scalability experiment; randomly rerun cell executions until the execution count is 2000.
    try:
        run_notebook_scale(notebook=args.notebook)
    except Exception as e:
        print(e)
