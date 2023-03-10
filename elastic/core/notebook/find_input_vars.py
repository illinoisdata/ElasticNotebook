from typing import List, Tuple
import dis
from ipykernel.zmqshell import ZMQInteractiveShell


def find_input_vars(cell: str, existing_variables: set) -> Tuple[set, dict]:
    """
        Captures the input variables of the cell.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
    """
    # Find first line where execution fails in given list and assign to break_line
    # line_numbers = []
    # for str in traceback_list:
    #     line_numbers.append(int(re.findall("line (\d+)", str)[0]))
    # break_line = min(line_numbers) if len(traceback_list) != 0 else -1
    # last_variables = []

    # Disassemble cell instructions
    instructions = dis.get_instructions(cell)

    input_variables = set()

    for instruction in instructions:

        # Input variable
        if instruction.opname == "LOAD_NAME" and (instruction.argrepr not in input_variables):
            if instruction.argrepr in existing_variables:
                input_variables.add(instruction.argrepr)

    return input_variables
