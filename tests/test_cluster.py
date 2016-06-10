from __future__ import print_function
import unittest
import pytraj as pt
from pytraj.utils import eq, aa_eq


class TestClustering(unittest.TestCase):

    def test_kmeans(self):
        from pytraj import cluster

        kmeans = cluster.kmeans
        traj = pt.iterload("data/tz2.nc", "data/tz2.parm7")

        cm = 'cluster kmeans clusters 10 @CA rms randompoint kseed 2 {0} noinfo'

        for sieve in [2, 3, 4]:
            sieve_str = "sieve {0} sieveseed 12".format(sieve)
            command = cm.format(sieve_str)
            state = pt.load_cpptraj_state(command, traj)
            state.run()

            data = kmeans(traj,
                          n_clusters=10,
                          kseed=2,
                          random_point=True,
                          metric='rms',
                          mask='@CA',
                          options=sieve_str)
            aa_eq(state.data[-2], data)

    def test_dbscan(self):
        command = """
        parm data/tz2.parm7
        trajin data/tz2.nc
        createcrd crd1
        cluster crdset crd1 C0 @CA dbscan epsilon 1.7 minpoints 5
        """

        state = pt.load_cpptraj_state(command)
        state.run()

        traj = pt.iterload("data/tz2.nc", "data/tz2.parm7")
        data = pt.cluster.dbscan(traj, mask='@CA', options='epsilon 1.7 minpoints 5')

        aa_eq(state.data[-2], data[0].values)

    def test_hieragglo(self):
        command = """
        parm data/tz2.parm7
        trajin data/tz2.nc
        createcrd crd1
        cluster crdset crd1 C0 !@H hieragglo epsilon 0.8 averagelinkage
        """

        state = pt.load_cpptraj_state(command)
        state.run()

        traj = pt.iterload("data/tz2.nc", "data/tz2.parm7")
        data = pt.cluster.hieragglo(traj, mask='!@H=', options='epsilon 0.8 averagelinkage summary sum.info')

        aa_eq(state.data[-2], data[0].values)

if __name__ == "__main__":
    unittest.main()
