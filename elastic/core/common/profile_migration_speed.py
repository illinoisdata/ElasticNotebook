#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import os, sys, time, random, string
import numpy as np
import pickle
import cProfile, pstats, io
from pstats import SortKey

def profile_migration_speed(dirname: str, alpha=1) -> float:
    """
        The migration speed is the sum of read and write speed (since we are writing the state to disk, then
        reading from disk to restore the notebook). The function should ideally be fast (<1 sec).
        Args:
            dirname: Location to profile.
    """
    filecount = 1
    #filesize = 1024 * 1024
    max_time = 0.8
    testing_dir = os.path.join(dirname, "measure_speed")
    os.system("rm -rf {} && mkdir {}".format(testing_dir, testing_dir))
    total_bytes = 0

    #test_str = string.ascii_letters
    start_time = time.time()

    total_read_time = 0
    total_write_time = 0
    for i in range(filecount):
        write_array_large = np.random.rand(10000, 10000)
        write_array_small = np.random.rand(100, 100)
        total_bytes += sys.getsizeof(write_array_large)
        total_bytes -= sys.getsizeof(write_array_small)

        write_start = time.time()
        out_file = open(os.path.join(testing_dir, str(i) + "large"), "wb")
        pickle.dump(write_array_large, out_file)
        out_file.close()
        total_write_time += time.time() - write_start
        print("total write:", total_write_time)

        read_start = time.time()
        in_file = open(os.path.join(testing_dir, str(i)) + "large", "rb")
        tmp = pickle.load(in_file)
        in_file.close()
        total_read_time += time.time() - read_start
        print("total read:", total_read_time)

        write_start = time.time()
        out_file = open(os.path.join(testing_dir, str(i) + "small"), "wb")
        pickle.dump(write_array_small, out_file)
        out_file.close()
        total_write_time -= time.time() - write_start
        print("total write:", total_write_time)

        read_start = time.time()
        in_file = open(os.path.join(testing_dir, str(i) + "small"), "rb")
        tmp = pickle.load(in_file)
        in_file.close()
        total_read_time -= time.time() - read_start
        print("total read:", total_read_time)

        if time.time() - start_time > max_time:
            break
    
    os.system("rm -rf {}".format(testing_dir))
    print("file size:", total_bytes)

    # empirical correction
    migration_speed_bps = total_bytes / (total_read_time + total_write_time * alpha)
    print("migration speed (bps):", migration_speed_bps)
    return migration_speed_bps
