from typing import List, Tuple
import dis
import ast
import inspect
from collections import deque
from ipykernel.zmqshell import ZMQInteractiveShell

# Node visitor for finding input variables.
class visitor(ast.NodeVisitor):
    def __init__(self, shell, shell_udfs):
        # Whether we are currently in local scope.
        self.is_local = False

        # Functions declared in 
        self.functiondefs = set()
        self.udfcalls = set()
        self.loads = set()
        self.globals = set()
        self.shell = shell
        self.udfs = shell_udfs

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # Only add as input if variable exists in current scope
            if not (self.is_local and node.id not in self.globals and node.id in self.shell.user_ns and type(self.shell.user_ns[node.id]) in {int, bool, str, float}):
                self.loads.add(node.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_AugAssign(self, node):
        # Only add as input if variable exists in current scope
        if not (self.is_local and node.target.id not in self.globals and node.target.id in self.shell.user_ns and type(self.shell.user_ns[node.target.id]) in {int, bool, str, float}):
            if isinstance(node.target, ast.Name):
                self.loads.add(node.target.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Global(self, node):
        for name in node.names:
            self.globals.add(name)
        ast.NodeVisitor.generic_visit(self, node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.udfcalls.add(node.func.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_FunctionDef(self, node):
        # Only add as input if variable exists in current scope
        self.is_local = True
        self.functiondefs.add(node.name)
        ast.NodeVisitor.generic_visit(self, node)
        self.is_local = False

def find_input_vars(cell: str, existing_variables: set, shell: ZMQInteractiveShell, shell_udfs: set) -> Tuple[set, dict]:
    """
        Captures the input variables of the cell.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
    """
    # Initialize ast walker
    v1 = visitor(shell = shell, shell_udfs = shell_udfs)

    # Disassemble cell instructions
    instructions = ast.parse(cell)

    input_variables = set()
    udf_calls = deque()
    udf_calls_visited = set()
    function_defs = set()

    v1.visit(instructions)

    input_variables = input_variables.union(v1.loads)
    function_defs = function_defs.union(v1.functiondefs)
    for udf in v1.udfcalls:
        if udf not in udf_calls_visited and udf in shell_udfs:
            udf_calls.append(udf)
            udf_calls_visited.add(udf)

    while udf_calls:
        v_nested = visitor(shell = shell, shell_udfs = shell_udfs)
        udf = udf_calls.popleft()
        instructions = ast.parse(inspect.getsource(shell.user_ns[udf]))
        v_nested.visit(instructions)

        # Update input variables and function definitions
        input_variables = input_variables.union(v_nested.loads)
        function_defs = function_defs.union(v_nested.functiondefs)
        for udf in v_nested.udfcalls:
            if udf not in udf_calls_visited and udf in shell_udfs:
                udf_calls.append(udf)
                udf_calls_visited.add(udf)

    input_variables = input_variables.intersection(existing_variables)
    return input_variables, function_defs
