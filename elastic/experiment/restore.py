from utils import restore_notebook, restore_notebook_pickle, restore_notebook_dump_session

import argparse

# Restore a notebook from a checkpoint file.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook", help="Notebook to run experiment on")
    parser.add_argument("-M", "--method", help="method")
    args = parser.parse_args()

    # Restore a pickle checkpoint file.
    if args.method == "pickle":
        try:
            restore_notebook_pickle(notebook=args.notebook)
        except Exception as e:
            print(e)

    # Restore a dumpsession checkpoint file.
    elif args.method == "dump":
        try:
            restore_notebook_dump_session(notebook=args.notebook)
        except Exception as e:
            print(e)

    # Restore an Elastic Notebook checkpoint file.
    else:
        try:
            restore_notebook(notebook=args.notebook, optimizer=args.method)
        except Exception as e:
            print(e)
