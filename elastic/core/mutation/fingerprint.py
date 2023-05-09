import pandas as pd
from elastic.core.mutation.id_graph import construct_id_graph, is_root_equals, is_structure_equals
from elastic.core.mutation.object_hash import UncomparableObj, ImmutableObj, NoneObj, NxGraphObj, \
    TorchTensorObj, ModuleObj, UnserializableObj, NpArrayObj, ScipyArrayObj, DataframeObj, \
    construct_object_hash
import time
from types import FunctionType

from collections.abc import Iterable

BASE_TYPES = [str, int, float, bool, type(None), FunctionType, ImmutableObj, UncomparableObj, NoneObj, NxGraphObj,
              TorchTensorObj, ModuleObj, UnserializableObj, NpArrayObj, ScipyArrayObj, DataframeObj]


def base_typed(obj, visited):
    """
        Recursive reflection method to convert any object property into a comparable form.
        From: https://stackoverflow.com/questions/1227121/compare-object-instances-for-equality-by-their-attributes
    """
    T = type(obj)
    from_numpy = T.__module__ == 'numpy'

    if T in BASE_TYPES or callable(obj) or (from_numpy and not isinstance(T, Iterable)):
        return obj

    visited.add(id(obj))

    if isinstance(obj, Iterable):
        return obj
    d = obj if T is dict else obj.__dict__

    comp_dict = {}
    for k, v in d.items():
        if id(v) not in visited:
            comp_dict[k] = base_typed(v, visited)

    return comp_dict


def deep_equals(*args):
    """
        Extended equality comparison which compares objects recursively by their attributes, i.e., it also works for
        certain user-defined objects with no equality (__eq__) defined.
    """
    return all(base_typed(args[0], set()) == base_typed(other, set()) for other in args[1:])


def construct_fingerprint(obj, profile_dict):
    """
        Construct a fingerprint of the object (ID graph + hash).
    """
    start = time.time()
    id_graph, id_set = construct_id_graph(obj)
    end = time.time()
    profile_dict["idgraph"] += end - start

    start = time.time()
    object_representation = construct_object_hash(obj, deepcopy=True)
    end = time.time()
    profile_dict["representation"] += end - start

    return [id_graph, id_set, object_representation]


def compare_fingerprint(fingerprint_list, new_obj, profile_dict, input_variables_id_graph_union):
    """
        Check whether an object has been changed by comparing it to its previous fingerprint.
    """
    changed = False
    overwritten = False
    uncomparable = False

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
        # Distinguish between overwritten variables and modified variables (i.e., x = 1 vs. x[0] = 1)
        if not is_root_equals(id_graph, fingerprint_list[0]):
            overwritten = True
        changed = True
        fingerprint_list[0] = id_graph
        fingerprint_list[1] = id_set

    end = time.time()
    profile_dict["idgraph"] += end - start

    # Value check via object hash: check whether the object's value has changed
    if not changed:
        start = time.time()
        try:
            new_repr = construct_object_hash(new_obj, deepcopy=False)

            # Variable is uncomparable
            if isinstance(new_repr, UncomparableObj):
                if id_set.intersection(input_variables_id_graph_union):
                    changed = True
                uncomparable = True
                fingerprint_list[2] = UncomparableObj()
            else:
                if not deep_equals(new_repr, fingerprint_list[2]):
                    # Variable has equality defined; the variable has been modified.
                    if "__eq__" in type(new_repr).__dict__.keys() or "eq" in type(new_repr).__dict__.keys():
                        changed = True
                    else:
                        # Object is uncomparable
                        if id_set.intersection(input_variables_id_graph_union):
                            changed = True
                        uncomparable = True
                        fingerprint_list[2] = UncomparableObj()
        except:
            # Variable is uncomparable
            if id_set.intersection(input_variables_id_graph_union):
                changed = True
            uncomparable = True
            fingerprint_list[2] = UncomparableObj()

    # Update the object hash if either:
    # 1. the object has been completely overwritten
    # 2. the object has been modified, and is of a comparable type (i.e., hashable or unhashable but has equality
    # defined)
    if overwritten or (changed and not uncomparable and not isinstance(fingerprint_list[2], UncomparableObj)):
        fingerprint_list[2] = construct_object_hash(new_obj, deepcopy=True)
    end = time.time()
    profile_dict["representation"] += end - start

    return changed, overwritten
