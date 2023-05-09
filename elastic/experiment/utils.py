from elastic.algorithm.selector import OptimizerType
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import time
import random

LOAD_EXT = """
import sys, os
import resource
max_rec = 0x100000

resource.setrlimit(resource.RLIMIT_STACK, [0x100 * max_rec, resource.RLIM_INFINITY])
sys.path.insert(0, os.path.abspath("../.."))
sys.setrecursionlimit(max_rec)
%load_ext ElasticNotebook
"""


def baseline_pickle_store(notebook_name):
    return """
import time
import sys, os
import dill
os.makedirs("/data/elastic-notebook/checkpoints/""" + notebook_name + """_pickle", exist_ok=True)
start = time.time()
my_list = %who_ls
for item in my_list:
    dill.dump(globals()[item], open("/data/elastic-notebook/checkpoints/""" + notebook_name + """_pickle/"+item+".pickle", "wb"))
end = time.time()
with open('/data/elastic-notebook/results/output_""" + notebook_name + """_pickle.txt', 'a') as f:
    f.write('\\nMigrate stage took - ' + repr(end - start) + " seconds" + '\\n')
"""


def baseline_pickle_load(notebook_name):
    return """
import time
import dill
import os
start_new = time.time()
for root, dirs, files in os.walk("/data/elastic-notebook/checkpoints/""" + notebook_name + """_pickle", topdown=False):
    for name in files:
        try:
            exec(name[:-7] +" = dill.load(open(os.path.join(root, name), 'rb'))")
        except:
            pass
end_new = time.time()
with open('/data/elastic-notebook/results/output_""" + notebook_name + """_pickle.txt', 'a') as f:
    f.write('\\nRecompute stage took - ' + repr(end_new - start_new) + " seconds" + '\\n')
"""


def baseline_criu(notebook_name):
    return """
import os, time
with open('/data/elastic-notebook/criu/""" + notebook_name + """.txt', 'w') as f:
    f.write(str(os.getpid()))
time.sleep(15000)
"""


def baseline_dump_session_store(notebook_name):
    return """
import time
import dill
start = time.time()
dill.dump_session('/data/elastic-notebook/checkpoints/""" + notebook_name + """.pickle_dump')
end = time.time()
with open('/data/elastic-notebook/results/output_""" + notebook_name + """_dump.txt', 'a') as f:
    f.write('\\nMigrate stage took - ' + repr(end - start) + " seconds" + '\\n')
"""


def baseline_dump_session_load(notebook_name):
    return """
import time
import dill
start_new = time.time()
dill.load_session('/data/elastic-notebook/checkpoints/""" + notebook_name + """.pickle_dump')
end_new = time.time()
with open('/data/elastic-notebook/results/output_""" + notebook_name + """_dump.txt', 'a') as f:
    f.write('\\nRecompute stage took - ' + repr(end_new - start_new) + " seconds" + '\\n')
"""


RECORD_EVENT = """
%%RecordEvent
"""

DIRECTORY = "notebooks/"

LOG_LOCATION = "/data/elastic-notebook/results"

MIGRATION_FILE_DIR = "/data/elastic-notebook/checkpoints/"


def set_optimizer(optimizer_name):
    return """
%SetOptimizer """ + optimizer_name + """
"""


def set_write_location(write_log_location):
    return """
%SetWriteLogLocation """ + write_log_location + """
"""


def set_notebook_name(notebook_name):
    return """
%SetNotebookName """ + notebook_name + """
"""


def set_migration_speed(migration_speed):
    return """
%SetMigrationSpeed """ + migration_speed + """
"""


def migrate_notebook(filename):
    return """
%Checkpoint """ + filename + """
"""


def load_checkpoint(filename):
    return """
%LoadCheckpoint """ + filename + """
"""


def run_notebook_baselines(notebook="numpy.ipynb"):
    """
       Run the specified notebook using baselines (pickle and dumpsession).
    """
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"
    # read notebook
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    # Add checkpointing code for the two baselines
    nb["cells"] += [nbformat.v4.new_code_cell(baseline_pickle_store(notebook)),
                    nbformat.v4.new_code_cell(baseline_dump_session_store(notebook))]

    # execute the updated notebook
    ep = ExecutePreprocessor(timeout=60000, kernel_name='python3')
    start = time.time()
    ep.preprocess(nb)
    end = time.time()
    return end - start


def run_notebook_raw(notebook="numpy.ipynb"):
    """
        Run the notebook without any modifications.
    """
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    start = time.time()
    ep = ExecutePreprocessor(timeout=60000, kernel_name='python3')
    ep.preprocess(nb)
    end = time.time()
    print("time: ", start - end)


def jumble(cells):
    random.shuffle(cells)
    return cells


def run_notebook_scale(notebook="numpy.ipynb"):
    """
        Augment the specified notebook to have 1000 cells and create a checkpoint using the optimizer after every
        100 cells.
    """
    # Experiment Code has code cells predefined
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"
    migration_speed = "150000000"  # bps

    # read notebook
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)
    cells = []

    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = RECORD_EVENT + cell["source"]
            cells.append(cell)

    # Inserting code to load ElasticNotebook magic class to the start of the notebook
    nb["cells"].insert(0, nbformat.v4.new_code_cell(LOAD_EXT))

    n = len(cells)
    total_cells = n
    loop = n
    while total_cells < 2100:
        if loop > 100:
            loop = loop % 100
            # Run optimizer and save results here
            nb["cells"] += [nbformat.v4.new_code_cell(set_optimizer("exact")),
                            nbformat.v4.new_code_cell(set_write_location(LOG_LOCATION)),
                            nbformat.v4.new_code_cell(set_notebook_name(notebook)),
                            nbformat.v4.new_code_cell(migrate_notebook(migration_file_name + "_" + "exact"))]
            print(len(nb["cells"]))
        new_cells = jumble(cells)
        nb["cells"] += new_cells

        total_cells += n
        loop += n
    ep = ExecutePreprocessor(timeout=6000, kernel_name='python3')
    ep.preprocess(nb)


def run_notebook(notebook="numpy.ipynb"):
    """
        Run the specified notebook and create a checkpoint using each optimizer.
    """
    # Experiment Code has code cells predefined
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"
    # migration_speed = "150000000"  # bps

    # read notebook
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    # Append "RecordEvent" magic function to all code cells
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = RECORD_EVENT + cell["source"]

    # Inserting code to load ElasticNotebook magic class to the start of the notebook
    nb["cells"].insert(0, nbformat.v4.new_code_cell(LOAD_EXT))

    # Add checkpointing code; checkpoint the notebook using the migration and restore-centric migration plans.
    for optimizer_enum in [OptimizerType.EXACT, OptimizerType.EXACT_R]:
        # Adding code to checkpoint notebook
        nb["cells"] += [nbformat.v4.new_code_cell(set_optimizer(optimizer_enum.value)),
                        nbformat.v4.new_code_cell(set_write_location(LOG_LOCATION)),
                        nbformat.v4.new_code_cell(set_notebook_name(notebook)),
                        nbformat.v4.new_code_cell(migrate_notebook(migration_file_name + "_" + optimizer_enum.value))]

    # execute the updated notebook
    ep = ExecutePreprocessor(timeout=60000, kernel_name='python3')
    ep.preprocess(nb)


def restore_notebook(notebook="numpy.ipynb", optimizer='exact'):
    """
        Restore a notebook from the specified checkpoint file from ElasticNotebook.
    """
    migration_file_name = MIGRATION_FILE_DIR + notebook + ".pickle"

    # Reconstruction
    nb_recover = nbformat.v4.new_notebook()
    nb_recover["cells"] += [nbformat.v4.new_code_cell(LOAD_EXT),
                            nbformat.v4.new_code_cell(set_optimizer(optimizer)),
                            nbformat.v4.new_code_cell(set_write_location(LOG_LOCATION)),
                            nbformat.v4.new_code_cell(set_notebook_name(notebook)),
                            nbformat.v4.new_code_cell(load_checkpoint(migration_file_name + "_" + optimizer))]

    ep = ExecutePreprocessor(timeout=60000, kernel_name='python3')
    ep.preprocess(nb_recover)


def restore_notebook_pickle(notebook="numpy_ipynb"):
    """
        Restore a notebook from a pickle checkpoint file.
    """
    nb_recover = nbformat.v4.new_notebook()
    nb_recover["cells"] += [nbformat.v4.new_code_cell(baseline_pickle_load(notebook))]

    ep = ExecutePreprocessor(timeout=6000, kernel_name='python3')
    ep.preprocess(nb_recover)


def restore_notebook_dump_session(notebook="numpy_ipynb"):
    """
        Restore a notebook from a dumpsession checkpoint file.
    """
    nb_recover = nbformat.v4.new_notebook()
    nb_recover["cells"] += [nbformat.v4.new_code_cell(baseline_dump_session_load(notebook))]

    ep = ExecutePreprocessor(timeout=6000, kernel_name='python3')
    ep.preprocess(nb_recover)


def run_notebook_criu(notebook="numpy_ipynb"):
    """
        Run a notebook for CRIU experiment; a sleep cell is added to the end of the notebook, which should be frozen
        by CRIU run by another process.
    """
    # read notebook
    with open(DIRECTORY + notebook) as f:
        nb = nbformat.read(f, as_version=4)

    # Add checkpointing code for each baseline
    nb["cells"] += [nbformat.v4.new_code_cell(baseline_criu(notebook))]

    ep = ExecutePreprocessor(timeout=86400, kernel_name='python3')
    ep.preprocess(nb)
