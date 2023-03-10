from inspect import isclass
from types import ModuleType
import dill


class IdGraphNode:
    """
        The IdGraph is used to model the reachable objects (their ids and types) from a given object.
    """

    def __init__(self, obj_id, obj_type, child_nodes):
        """
            Args:
                obj_id: id (memory address) of the object.
                obj_type: type of the object.
                child_nodes: other objects reachable from this object (i.e. class attributes, list/set members)
        """
        self.obj_id = obj_id
        self.obj_type = obj_type
        self.child_nodes = child_nodes


def construct_id_graph_node(obj, visited):
    """
        Helper function for constructing an ID graph. Constructs an ID graph node and recurses into reachable objects
        in BFS fashion.
        Args:
            obj: object.
            visited (set): set of visited objects (for handling cyclic references).
    """
    if obj is None:
        return None

    child_list = []
    id_graph_node = IdGraphNode(id(obj), type(obj).__name__, child_list)

    visited[id(obj)] = id_graph_node

    # obj is object instance: recurse into attributes
    # Special note for sets: this works as the order of iterating through sets in the same session is deterministic.
    if not isinstance(obj, ModuleType) and not isclass(obj) and hasattr(obj, '__dict__'):
        for k, v in vars(obj).items():
            if id(v) in visited:
                child_list.append(visited[id(v)])
            else:
                child_list.append(construct_id_graph_node(v, visited))

    # obj is Iterable: recurse into items
    elif type(obj) in [list, tuple, set]:
        for child_obj in obj:
            if id(child_obj) in visited:
                child_list.append(visited[id(child_obj)])
            else:
                child_list.append(construct_id_graph_node(child_obj, visited))

    # obj is dictionary: recurse into both keys and values
    elif type(obj) is dict:
        for k, v in obj.items():
            if id(k) in visited:
                child_list.append(visited[id(k)])
            else:
                child_list.append(construct_id_graph_node(k, visited))
            if id(v) in visited:
                child_list.append(visited[id(v)])
            else:
                child_list.append(construct_id_graph_node(v, visited))

    return id_graph_node


def construct_id_graph(obj):
    """
        Construct the ID graph for an object.
        Returns:
            graph_bytestring (bytestring): the serialized bytestring of the ID graph.
            visited: a set of all IDs of reachable objects in the graph. For checking object overlaps.
    """
    visited = {}
    graph_bytestring = dill.dumps(construct_id_graph_node(obj, visited))
    return graph_bytestring, set(visited.keys())
