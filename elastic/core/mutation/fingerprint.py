import pandas as pd
import numpy as np
from elastic.core.mutation.id_graph import construct_id_graph, is_root_equals, is_structure_equals
from elastic.core.mutation.object_representation import construct_object_representation
import time

from collections.abc import Iterable

BASE_TYPES = [str, int, float, bool, type(None)]


def base_typed(obj):
    """Recursive reflection method to convert any object property into a comparable form.
    """
    T = type(obj)
    from_numpy = T.__module__ == 'numpy'

    if T in BASE_TYPES or callable(obj) or (from_numpy and not isinstance(T, Iterable)):
        return obj

    if isinstance(obj, Iterable):
        base_items = [base_typed(item) for item in obj]
        return base_items if from_numpy else T(base_items)

    d = obj if T is dict else obj.__dict__

    return {k: base_typed(v) for k, v in d.items()}


def deep_equals(*args):
    return all(base_typed(args[0]) == base_typed(other) for other in args[1:])

def construct_fingerprint(obj, profile_dict):
    """
        A fingerprint of the object consists of its ID graph and its object representation (i.e. value).
    """
    start = time.time()
    id_graph, id_set = construct_id_graph(obj)
    end = time.time()
    profile_dict["idgraph"] += end - start

    start = time.time()
    object_representation = construct_object_representation(obj, deepcopy=True)
    end = time.time()
    profile_dict["representation"] += end - start

    return [id_graph, id_set, object_representation]


def compare_fingerprint(fingerprint_list, new_obj, profile_dict, input_variables_id_graph_union):
    """
        Check whether an object has been changed by comparing it to its previous fingerprint.
    """
    changed = False
    overwritten = False

    # Hack: check for pandas dataframes and series: if the flag has been flipped back on, the object has been changed.
    if isinstance(new_obj, pd.DataFrame):
        for (_, col) in new_obj.items():
            if col.__array__().flags.writeable:
                changed = True
                break

    elif isinstance(new_obj, pd.Series):
        if new_obj.__array__().flags.writeable:
            changed = True

    # ID graph check: check whether the structure of the object has changed (i.e. its relation with other objects)
    start = time.time()
    id_graph, id_set = construct_id_graph(new_obj)
    if id_set != fingerprint_list[1] or not is_structure_equals(id_graph, fingerprint_list[0]):
        if not is_root_equals(id_graph, fingerprint_list[0]):
            overwritten = True
        changed = True
        fingerprint_list[0] = id_graph
        fingerprint_list[1] = id_set
    end = time.time()
    profile_dict["idgraph"] += end - start

    # Value check: check whether the object's value has changed
    start = time.time()
    try:
        if not deep_equals(construct_object_representation(new_obj, deepcopy=False), fingerprint_list[2]):
            changed = True
    except:
        # Variable is uncomparable
        if id_set.intersection(input_variables_id_graph_union):
            changed = True

    if changed:
        fingerprint_list[2] = construct_object_representation(new_obj, deepcopy=True)

    end = time.time()
    profile_dict["representation"] += end - start
    return changed, overwritten
