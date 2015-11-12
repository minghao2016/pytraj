# distutils: language = c++
from cython.operator cimport dereference as deref

from ..externals.six import string_types
from ..action_dict import ActionDict
from .._shared_methods import iterframe_master

def _get_arglist(arg):
    if isinstance(arg, ArgList):
        return arg
    else:
        return ArgList(arg)

def create_pipeline(traj, commands, DatasetList dslist=DatasetList(), frame_indices=None):
    '''create frame iterator from cpptraj's commands.

    This method is useful if you want cpptraj pre-processing your Trajectory before
    throwing it to your own method.

    Parameters
    ----------
    commands : a list of strings of cpptraj's Action commands
    traj : Trajectory or any iterable that produces Frame
    dslist : CpptrajDatasetList, optional

    Examples
    --------
    >>> import pytraj as pt
    >>> traj = pt.load_sample_data('tz2')
    >>> for frame in pt.create_pipeline(traj, ['autoimage', 'rms', 'center :1']): print(frame)

    Above example is similiar to cpptraj's command::
     
         cpptraj -i EOF<<
         parm tz2.ortho.parm
         trajin tz2.ortho.nc
         autoimage
         rms
         center :1
         EOF

    You can desire your own method::

        def new_method(traj, ...):
            for frame in traj:
                do_some_thing_fun_with(frame)

        fi = pt.create_pipeline(traj, ['autoimage', 'rms', 'center :1'])

        # perform action with pre-processed frames (already autoimaged, then rms fit to
        # 1st frame, then center at box center.
        data = new_method(fi, ...)
    '''
    cdef Frame frame
    cdef ActionList actlist

    if frame_indices is None:
        fi = traj
    else:
        fi = traj.iterframe(frame_indices=frame_indices)

    if isinstance(commands, (list, tuple)):
        commands = commands
    elif isinstance(commands, string_types):
        commands = [line.lstrip().rstrip() for line in commands.split('\n') if line.strip() != '']

    actlist = ActionList(commands, top=traj.top, dslist=dslist) 
    for frame in iterframe_master(fi):
        actlist.do_actions(frame)
        yield frame


def do(lines, traj, *args, **kwd):
    cdef DatasetList dslist


    if isinstance(lines, (list, tuple)):
        ref = kwd.get('ref')
        if ref is not None:
            if isinstance(ref, Frame):
                reflist = [ref, ]
            else:
                # list/tuplex
                reflist = ref
        else:
            reflist = []

        dslist = DatasetList()

        if reflist:
            for ref_ in reflist:
                ref_dset = dslist.add_new('reference')
                ref_dset.top = traj.top
                ref_dset.add_frame(ref_)

        # create Frame generator
        fi = create_pipeline(traj, commands=lines, dslist=dslist)

        # just iterate Frame to trigger calculation.
        for _ in fi:
            pass

        # remove ref
        return dslist[len(reflist):].to_dict()

    elif callable(lines):
        return lines(traj, *args, **kwd)


cdef class ActionList:
    def __cinit__(self):
        self.thisptr = new _ActionList()
        self.top_is_processed = False

    property data:
        def __get__(self):
            return self._dslist

    def __init__(self, commands=None, Topology top=None,
                 DatasetList dslist=DatasetList(), DataFileList dflist=DataFileList(),
                 crdinfo={}):
        """not done yet

        Parameters
        ----------
        actionlist : a list of tuple
        top : Topology
        dslist : DatasetList, optional
            hold data for actions
        dflist : DataFileList, optional
            hold datafiles

        Examples
        --------
        >>> import pytraj as pt
        >>> from pytraj import ActionList
        >>> list_of_commands = ['autoimage',
                                'rmsd first @CA',
                                'hbond :3,8,10']
        >>> alist = ActionList(list_of_commands, traj.top, dslist=dslist)
        >>> for frame in traj:
        >>>     alist.do_actions(frame)
        """
        self._dslist = dslist
        self._dflist = dflist
        self._crdinfo = crdinfo

        if commands is not None and top is not None:
            for command in commands:
                command = command.rstrip().lstrip()
                try:
                    action, cm = command.split(" ", 1)
                except ValueError:
                    action = command.split(" ", 1)[0]
                    cm = ''
                action = action.rstrip().lstrip()
                self.add_action(action, command=cm,
                                top=top, dslist=dslist, dflist=dflist)

    def __dealloc__(self):
        if self.thisptr:
            del self.thisptr

    def clear(self):
        self.thisptr.Clear()

    def add_action(self, action="", 
                         command="", 
                         top=None, 
                         DatasetList dslist=DatasetList(), 
                         DataFileList dflist=DataFileList(),
                         check_status=False):
        """Add action to ActionList

        Parameters
        ----------
        action : str or Action object
        command : str or ArgList object
        top : str | Topology | TopologyList
        dslist : DatasetList 
        dflist : DataFileList
        check_status : bool, default=False
            return status of Action (0 or 1) if "True"
        """
        cdef object _action
        cdef int status
        cdef _ActionInit actioninit_
        actioninit_ = _ActionInit(dslist.thisptr[0], dflist.thisptr[0])

        if isinstance(action, string_types):
            # create action object from string
            _action = ActionDict()[action]
        else:
            _action = action

        cdef FunctPtr func = <FunctPtr> _action.alloc()
        cdef ArgList _arglist

        self.top = top
        # add function pointer: How?

        _arglist = _get_arglist(command)
        status = self.thisptr.AddAction(func.ptr, _arglist.thisptr[0], 
                                        actioninit_)

        if check_status:
            # return "0" if sucess "1" if failed
            return status
        else:
            return None

    def process(self, Topology top, crdinfo={}, n_frames_t=0, bint exit_on_error=True):
        # let cpptraj free mem
        cdef _ActionSetup actionsetup_
        cdef CoordinateInfo crdinfo_
        cdef Box box
        cdef bint has_velocity, has_time, has_force

        if not crdinfo:
            crdinfo = self._crdinfo
        else:
            crdinfo = crdinfo

        box = crdinfo.get('box', top.box)
        has_velocity = crdinfo.get('has_velocity', False)
        has_time = crdinfo.get('has_time', False)
        has_force = crdinfo.get('has_force', False)

        crdinfo_ = CoordinateInfo(box.thisptr[0], has_velocity, has_time, has_force)

        #top._own_memory = False

        actionsetup_ = _ActionSetup(top.thisptr, crdinfo_, n_frames_t)
        self.thisptr.SetupActions(actionsetup_, exit_on_error)

    def do_actions(self, traj=Frame(), int idx=0, mass=True):
        cdef _ActionFrame actionframe_
        cdef Frame frame
        cdef int i

        if not self.top_is_processed:
            self.process(self.top)
            # make sure to make top_is_processed True after processing
            # if not, pytraj will try to setup for every Frame
            self.top_is_processed = True

        if isinstance(traj, Frame):
            frame = <Frame> traj
            # only set mass for Frame that is used as a pointer
            # else: do not need to set mass (eg. Frame produced by TrajectoryIterator
            # since it's already set mass
            if mass and frame._as_view:
                frame.set_mass(self.top)
            actionframe_ = _ActionFrame(frame.thisptr)
            self.thisptr.DoActions(idx, actionframe_)
        else:
            for i, frame in enumerate(iterframe_master(traj)):
                self.do_actions(frame, i) 

    def is_empty(self):
        return self.thisptr.Empty()

    @property
    def n_actions(self):
        return self.thisptr.Naction()
