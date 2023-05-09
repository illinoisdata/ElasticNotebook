from utils import run_notebook, run_notebook_baselines
import argparse

# Python script for running and checkpointing a notebook.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook", help="Notebook to run experiment on")
    args = parser.parse_args()

    # Run the notebook with Elastic Notebook enabled and generate Elastic Notebook checkpoint files.
    try:
        run_notebook(notebook=args.notebook)
    except Exception as e:
        print(e)

    # Run the notebook as is, and generate checkpoint files with Pickle and Dumpsession.
    try:
        runtime = run_notebook_baselines(notebook=args.notebook)
    except Exception as e:
        print(e)

    # Notebook runtime.
    print("exec time:", runtime)
