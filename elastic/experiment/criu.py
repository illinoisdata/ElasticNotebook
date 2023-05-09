from utils import run_notebook_criu
import argparse
import os


# Start a notebook thread for checkpointing with CRIU.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-N", "--notebook", help="Notebook to run experiment on")
    args = parser.parse_args()

    with open('/data/elastic-notebook/criu/'+args.notebook+'_master.txt', 'w') as f:
        f.write(str(os.getpid()))
        print(os.getpid())

    try:
        run_notebook_criu(notebook=args.notebook)
    except Exception as e:
        print(e)
        with open('/data/elastic-notebook/criu/'+args.notebook+'.txt', 'w') as f:
            f.write("echo \"a\"")
    print("Done")
