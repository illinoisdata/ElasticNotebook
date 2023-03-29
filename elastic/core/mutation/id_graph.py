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


def is_primitive(obj_type):
    return obj_type in {int, float, bool, str}

def is_root_equals(node1, node2):
    if node1 is None and node2 is None:
        return True
    elif node1 is None or node2 is None:
        return False
    return node1.obj_id == node2.obj_id and node1.obj_type == node2.obj_type

def is_structure_equals_helper(node1, node2, visited):
    if node1.obj_id != node2.obj_id or node1.obj_type != node2.obj_type or len(node1.child_nodes) != len(node2.child_nodes):
        return False
    visited.add(node1)

    for i in range(len(node1.child_nodes)):
        if node1.child_nodes[i] in visited:
            continue
        if not is_structure_equals_helper(node1.child_nodes[i], node2.child_nodes[i], visited):
            return False

    return True

def is_structure_equals(node1, node2):
    if node1 is None and node2 is None:
        return True
    elif node1 is None or node2 is None:
        return False
    return is_structure_equals_helper(node1, node2, set())

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
            if k.startswith("_"):
                continue
            if v is None or is_primitive(type(v)):
                continue

            if id(v) in visited:
                child_list.append(visited[id(v)])
            else:
                child_list.append(construct_id_graph_node(v, visited))

    # obj is Iterable: recurse into items
    if type(obj) in [list, tuple, set]:
        for child_obj in obj:
            if child_obj is None or is_primitive(type(child_obj)):
                continue
            if id(child_obj) in visited:
                child_list.append(visited[id(child_obj)])
            else:
                child_list.append(construct_id_graph_node(child_obj, visited))

    # obj is dictionary: recurse into both keys and values
    elif type(obj) is dict:
        for k, v in obj.items():
            if k is None or is_primitive(type(k)):
                continue
            if id(k) in visited:
                child_list.append(visited[id(k)])
            else:
                child_list.append(construct_id_graph_node(k, visited))
            if v is None or is_primitive(type(v)):
                continue
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
    graph = construct_id_graph_node(obj, visited)
    return graph, set(visited.keys())
