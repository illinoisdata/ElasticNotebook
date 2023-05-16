import unittest
import os
import pickle
from pathlib import Path

from elastic.core.io.filesystem_adapter import FilesystemAdapter

TEST_FILE_PATH = "./tmp_test_file"
KEY = "project"
VALUE = "elastic-notebook"


class TestFilesystemAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = FilesystemAdapter()
        self.fpath = Path(TEST_FILE_PATH)
    

    def tearDown(self) -> None:
        self.adapter.remove(self.fpath)
        self.assertFalse(os.path.exists(self.fpath))

    def test_create(self):
        self.adapter.create(self.fpath)
        self.assertTrue(os.path.exists(self.fpath))

    def test_read_all(self):
        s = pickle.dumps({KEY: VALUE})
        with open(self.fpath, "wb") as fd:
            fd.write(s)
        
        s_read = self.adapter.read_all(self.fpath)
        self.assertEqual(VALUE, s_read[KEY])
        

if __name__ == '__main__':
    unittest.main()
