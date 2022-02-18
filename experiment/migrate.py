#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.common.migration_metadata import MigrationMetadata
from elastic.io.external_storage import ExternalStorage

def migrate(objects_to_migrate, 
            metadata: MigrationMetadata, 
            storage: ExternalStorage):
    """
    (1) Iterate over all objects in `objects_to_migrate`. For each object
        (1a) Pickle the object
        (1b) Write to external storage
    (2) Write metadata to external storage

    Args:
        objects_to_migrate (List):
            a list of python objects to migrate
        metadata (MigrationMetadata):
            a JSON file containing migration metadata
        external_storage (ExternalStorage):
            a wrapper for any storage adapter (local fs, cloud storage, etc.)
    """
    pass