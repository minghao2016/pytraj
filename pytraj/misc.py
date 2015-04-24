"""this file has commonly used actions such as rmsd calculation, 
randomizeions, strip atoms, ..."""

from __future__ import print_function, absolute_import
from pytraj.Topology import Topology
from .TopologyList import TopologyList
from .ArgList import ArgList
from pytraj.Frame import Frame
#from pytraj.Trajin_Single import Trajin_Single
from pytraj.FrameArray import FrameArray
from pytraj.actions import allactions
from pytraj import adict, analdict
from pytraj.DataSetList import DataSetList

from pytraj._utils import set_world_silent

# external
from pytraj.externals.six import string_types

def to_amber_mask(txt):
    import re
    """Convert something like 'ASP_16@OD1-ARG_18@N-H to ':16@OD1 :18@H'"""

    if isinstance(txt, string_types):
        txt = txt.replace("_", ":")
        return " ".join(re.findall(r"(:\d+@\w+)", txt))
    elif isinstance(txt, (list, tuple)):
        for i, _txt in enumerate(txt):
            txt[i] = to_amber_mask(_txt)
        return txt
    else:
        raise NotImplementedError()

def info(obj):
    """get `help` for obj
    Useful for Actions and Analyses
    
    Since we use `set_worl_silent` to turn-off cpptraj' stdout, we need 
    to turn on to use cpptraj's help methods
    """
    if isinstance(obj, string_types):
        if obj in adict.keys():
            # make Action object
            _obj = adict[obj]
        elif obj in analdict.keys():
            # make Analysis object
            _obj = analdict[obj]
        else:
            raise ValueError("keyword must be an Action or Analysis")
    else:
        # assume `obj` hasattr `help`
        _obj = obj

    if hasattr(_obj, 'help'):
        set_world_silent(False)
        _obj.help()
        set_world_silent(True)
    else:
        raise ValueError("object does not have `help` method")

def get_action_dict():
    actdict = {}
    for key in allactions.__dict__.keys():
        if "Action_" in key:
            act = key.split("Action_")[1]
            # add Action classes
            actdict[act] = allactions.__dict__["Action_" + act]
    return actdict

# add action_dict
action_dict = get_action_dict()

def show_code(func, get_txt=False):
    """show code of func or module"""
    import inspect
    txt = inspect.getsource(func)
    if not get_txt:
        print (txt)
    else:
        return txt

def get_atts(obj):
    """get methods and atts from obj but excluding special methods __"""
    atts_dict = dir(obj)
    return [a for a in atts_dict if not a.startswith("__")]
