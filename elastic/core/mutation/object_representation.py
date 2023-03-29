import mmap
from inspect import isclass
from types import GeneratorType
from types import ModuleType

import dill
import pandas as pd
import polars as pl
import lightgbm
import numpy as np
import scipy
import torch
import copy

# Object representing none.
class NoneObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, NoneObj):
            return True
        return False

# Object representing a dataframe.
class DataframeObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, DataframeObj):
            return True
        return False

class NpArrayObj:
    def __init__(self, array):
        self.array = array
        pass

    def __eq__(self, other):
        if isinstance(other, NpArrayObj):
            try:
                return np.array_equal(self.array, other.array, equal_nan=True)
            except:
                return np.array_equal(self.array, other.array)
        return False

class ScipyArrayObj:
    def __init__(self, array):
        self.array = array
        pass

    def __eq__(self, other):
        if isinstance(other, ScipyArrayObj):
            if self.array.shape != other.array.shape:
                return False
            return (self.array != other.array).nnz==0
        return False

class TorchTensorObj:
    def __init__(self, array):
        self.array = array
        pass

    def __eq__(self, other):
        if isinstance(other, TorchTensorObj):
            return torch.equal(self.array, other.array)
        return False

class ModuleObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, ModuleObj):
            return True
        return False

# Object representing general unserializable class.
class UnserializableObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, UnserializableObj):
            return True
        return False


def construct_object_representation(obj, deepcopy=False):
    """
        Construct a representation for the object.
    """
    if obj is None:
        return NoneObj()

    if isclass(obj):
        return type(obj)

    # Flag hack for Pandas dataframes: each dataframe column is a numpy array.
    # All the writeable flags of these arrays are set to false; if after cell execution, any of these flags are
    # reset to True, we assume that the dataframe has been modified.
    if isinstance(obj, pd.DataFrame):
        for (_, col) in obj.items():
            col.__array__().flags.writeable = False
        return DataframeObj()

    if isinstance(obj, pd.Series):
        obj.__array__().flags.writeable = False
        return DataframeObj()

    if isinstance(obj, np.ndarray):
        if deepcopy:
            return NpArrayObj(copy.deepcopy(obj))
        else:
            return NpArrayObj(obj)

    if isinstance(obj, scipy.sparse.csr_matrix):
        if deepcopy:
            return ScipyArrayObj(copy.deepcopy(obj))
        else:
            return NpArrayObj(obj)

    if isinstance(obj, torch.Tensor):
        if deepcopy:
            return TorchTensorObj(copy.deepcopy(obj))
        else:
            return TorchTensorObj(obj)

    if isinstance(obj, ModuleType):
        return ModuleObj()

    # Polars dataframes are immutable.
    if isinstance(obj, pl.DataFrame):
        return type(obj)

    # LightGBM dataframes are immutable.
    if isinstance(obj, lightgbm.Dataset):
        return type(obj)

    # Try to serialize the object
    try:
        if deepcopy:
            return copy.deepcopy(obj)
        else:
            return obj
    except:
        return UnserializableObj()
