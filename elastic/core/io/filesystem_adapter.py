from pathlib import Path
from elastic.core.io.adapter import Adapter
import dill
import gc


class FilesystemAdapter(Adapter):
    def __init__(self):
        super().__init__()

    def read_all(self, path: Path):
        """
            The following (read then decode) is faster vs. directly returning dill.load when network speed is low.
        """
        gc.disable()
        contents_bytestring = open(path, "rb").read()
        contents = dill.loads(contents_bytestring)
        gc.enable()
        return contents

    def create(self, path: Path):
        path.touch()

    def write_all(self, path: Path, buf):
        dill.dump(buf, open(path, "wb"))

    def remove(self, path: Path):
        path.unlink()
