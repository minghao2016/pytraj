#!/usr/bin/env python

from __future__ import print_function
import unittest
import numpy as np
import pytraj as pt
from pytraj.utils import eq, aa_eq

command = '''
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


class TestProjection(unittest.TestCase):

    def test_projection(self):
        traj = pt.load("./data/tz2.nc", "./data/tz2.parm7")

        state = pt.load_cpptraj_state(command)
        state.run()
        cpp_modes = state.data['MyEvecs']
        cpp_arr_crd = np.array(cpp_modes._get_avg_crd())
        cpp_arr_crd = cpp_arr_crd.reshape(117, 3)

        mask = '!@H='
        pt.superpose(traj, mask=mask)
        avg = pt.mean_structure(traj)
        atom_indices = traj.top(mask).indices
        strip_avg_coords = avg.xyz[atom_indices]
        pt.superpose(traj, mask=mask, ref=avg)
        avg2 = pt.mean_structure(traj, mask=mask)

        mat = pt.matrix.covar(traj, mask)
        modes = pt.matrix.diagonalize(mat, n_vecs=2)[0]

        aa_eq(cpp_arr_crd, avg2.xyz)

        aa_eq(modes.eigenvalues, state.data['MyEvecs'].eigenvalues)
        aa_eq(modes.eigenvectors, state.data['MyEvecs'].eigenvectors)

        projection_data = pt.common_actions._projection(traj, mask=mask, average_coords=avg2.xyz,
                                                        eigenvalues=modes.eigenvalues, 
                                                        eigenvectors=modes.eigenvectors,
                                                        scalar_type='covar')
        aa_eq(projection_data, state.data[-2:].values)

if __name__ == "__main__":
    unittest.main()
