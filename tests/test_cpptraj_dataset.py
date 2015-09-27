#!/usr/bin/env python
from __future__ import print_function
import unittest
import pytraj as pt
from pytraj.utils import eq, aa_eq

# used for loading cpptraj state
txt = '''
# Step one. Generate average structure.
# RMS-Fit to first frame to remove global translation/rotation.
parm data/tz2.parm7
trajin data/tz2.nc
rms first !@H=
average crdset AVG
run
# Step two. RMS-Fit to average structure. Calculate covariance matrix.
# Save the fit coordinates.
rms ref AVG !@H=
matrix covar name MyMatrix !@H=
createcrd CRD1
run
# Step three. Diagonalize matrix.
runanalysis diagmatrix MyMatrix vecs 2 name MyEvecs
# Step four. Project saved fit coordinates along eigenvectors 1 and 2
crdaction CRD1 projection evecs MyEvecs !@H= out project.dat beg 1 end 2
'''

class TestCpptrajDataset(unittest.TestCase):
    def test_dataset_coords_ref(self):
        traj = pt.iterload('data/tz2.nc', 'data/tz2.parm7')
        avg_frame = pt.mean_structure(traj(rmsfit=(0, '!@H=')))
        state = pt.datafiles.load_cpptraj_state(txt)
        state.run()

        # need to loop several times to make sure this does not fail
        # due to memory free
        for _ in range(20):
            cpp_ref = state.data['AVG']
            aa_eq(avg_frame.xyz, cpp_ref.xyz)
            aa_eq(avg_frame.xyz, cpp_ref.values)
            aa_eq(avg_frame.xyz, cpp_ref.data)


if __name__ == "__main__":
    unittest.main()