#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from pathlib import Path
from elastic.core.io.adapter import Adapter
import dill

class FilesystemAdapter(Adapter):
    def __init__(self):
        pass

    def read_all(self, path: Path):
        return dill.load(open(path, "rb"))

    def create(self, path: Path):
        path.touch()

    def write_all(self, path: Path, buf):
        dill.dump(buf, open(path, "wb"))

    def remove(self, path: Path):
        path.unlink()
