

def find_created_deleted_vars(pre_execution, post_execution):
    created_variables = set()
    deleted_variables = set()

    # New variables
    for varname in post_execution.difference(pre_execution):
        if not varname.startswith('_'):
            created_variables.add(varname)

    # Deleted variables
    for varname in pre_execution.difference(post_execution):
        if not varname.startswith('_'):
            deleted_variables.add(varname)

    return created_variables, deleted_variables
