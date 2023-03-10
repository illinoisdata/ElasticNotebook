import mmap
from inspect import isclass
from types import GeneratorType

import dill
import pandas as pd
# import polars as pl
# import lightgbm


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

# Object representing general unserializable class.
class UnserializableObj:
    def __init__(self, representation):
        self.representation = representation

    def __eq__(self, other):
        if isinstance(other, UnserializableObj):
            return self.representation == other.representation
        return False


def construct_object_representation(obj):
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

    # # Polars dataframes are immutable.
    # if isinstance(obj, pl.DataFrame):
    #     return type(obj)

    # # LightGBM dataframes are immutable.
    # if isinstance(obj, lightgbm.Dataset):
    #     return type(obj)

    # # TODO: LookForward hack for generators
    # elif isinstance(obj, tf.random.Generator):

    # Since mmaps are unserializable, we use its pointer position to check whether it has been mutated.
    if isinstance(obj, mmap.mmap):
        return UnserializableObj(mmap.tell())

    # Try to serialize the object
    try:
        return dill.dumps(obj)
    except:
        return UnserializableObj(NoneObj())
