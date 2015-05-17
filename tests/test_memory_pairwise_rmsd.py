from __future__ import print_function
from pytraj import io as mdio
import pytraj.common_actions as pyca
from pytraj.testing import aa_eq

@profile
def test_0():
# Result:
#Line #    Mem usage    Increment   Line Contents
#================================================
#     6   42.766 MiB    0.000 MiB   @profile
#     7                             def test_0():
#     8   56.176 MiB   13.410 MiB       traj = mdio.iterload("data/nogit/tip3p/md.trj", "./data/nogit/tip3p/tc5bwat.top")
#     9  250.113 MiB  193.938 MiB       return pyca.calc_pairwise_rmsd(traj(1, 1000), '@CA', traj.top, dtype='ndarray')
    traj = mdio.iterload("data/nogit/tip3p/md.trj", "./data/nogit/tip3p/tc5bwat.top")
    return pyca.calc_pairwise_rmsd(traj(1, 1000), '@CA', traj.top, dtype='ndarray')

@profile
def test_1():
#Line #    Mem usage    Increment   Line Contents
#================================================
#    18   42.766 MiB    0.000 MiB   @profile
#    19                             def test_1():
#    20                                 # use much less memory since we strip atoms in the fly
#    21                                 # 62.965 MiB
#    22   56.176 MiB   13.410 MiB       traj = mdio.iterload("data/nogit/tip3p/md.trj", "./data/nogit/tip3p/tc5bwat.top")
#    23   56.176 MiB    0.000 MiB       new_top = traj.top.strip_atoms("!@CA", copy=True)
#    24   63.965 MiB    7.789 MiB       return pyca.calc_pairwise_rmsd(traj(1, 1000, mask='@CA'), top=new_top, dtype='ndarray')

    # use much less memory since we strip atoms in the fly
    # 62.965 MiB
    traj = mdio.iterload("data/nogit/tip3p/md.trj", "./data/nogit/tip3p/tc5bwat.top")
    new_top = traj.top.strip_atoms("!@CA", copy=True)
    return pyca.calc_pairwise_rmsd(traj(1, 1000, mask='@CA'), top=new_top, dtype='ndarray')

if __name__ == "__main__":
    # make sure to turn on ONLY one test
    #arr0 = test_0()
    arr1 = test_1()
    #aa_eq(arr0, arr1)