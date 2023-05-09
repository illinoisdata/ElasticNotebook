class VariableSnapshot:
    """
        A variable snapshot in the dependency graph corresponds to a version of a variable.
        I.e. if variable 'x' has been assigned 3 times (x = 1, x = 2, x = 3), then 'x' will have 3 corresponding
        variable snapshots.
    """
    def __init__(self, name: str, version: int, deleted: bool):
        """
            Create a variable snapshot from variable properties.
            Args:
                name (str): Variable name.
                version (int): The nth update to the corresponding variable.
                deleted (bool): Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """
        self.name = name
        self.version = version

        # Whether this VS corresponds to a deleted variable.
        # i.e. if this VS was created for 'del x' we set this to true so this variable is explicitly not considered
        # for migration.
        self.deleted = deleted

        # Cell executions accessing this variable snapshot (i.e. require this variable snapshot to run).
        self.input_ces = []

        # The unique cell execution creating this variable snapshot.
        self.output_ce = None

        # Size of variable pointed to by VS; estimated at migration time.
        self.size = 0


