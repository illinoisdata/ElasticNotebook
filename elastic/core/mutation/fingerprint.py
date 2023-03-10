import pandas as pd

from elastic.core.mutation.id_graph import construct_id_graph
from elastic.core.mutation.object_representation import construct_object_representation


def construct_fingerprint(obj):
    """
        A fingerprint of the object consists of its ID graph and its object representation (i.e. value).
    """
    id_graph_bytestring, id_set = construct_id_graph(obj)
    object_representation = construct_object_representation(obj)

    return id_graph_bytestring, id_set, object_representation


def compare_fingerprint(fingerprint_tuple, new_obj):
    """
        Check whether an object has been changed by comparing it to its previous fingerprint.
    """
    changed = False

    # Check for pandas dataframes and series: if the flag has been flipped back on, the object has been changed.
    if isinstance(new_obj, pd.DataFrame):
        for (_, col) in new_obj.items():
            if col.__array__().flags.writeable:
                changed = True
                break

    elif isinstance(new_obj, pd.Series):
        if new_obj.__array__().flags.writeable:
            changed = True

    id_graph_bytestring, id_set = construct_id_graph(new_obj)
    object_representation = construct_object_representation(new_obj)

    if id_graph_bytestring != fingerprint_tuple[0] or id_set != fingerprint_tuple[1] or \
            object_representation != fingerprint_tuple[2]:
        changed = True

    return changed, (id_graph_bytestring, id_set, object_representation)
