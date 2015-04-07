import unittest
from pytraj.base import *
from pytraj import io as mdio
from pytraj.utils.check_and_assert import assert_almost_equal

class Test(unittest.TestCase):
    def test_0(self):
        try:
            import mdtraj as md
            has_mdtraj = True
        except ImportError:
            has_mdtraj = False

        if has_mdtraj:
            mtop = md.load_prmtop("./data/Tc5b.top")
            print(mtop)

            pseudotop = Topology()
            for mdatom in mtop.atoms:
                atom = Atom(mdatom.name, mdatom.name)
                mdres = mdatom.residue
                pseudotop.add_atom(atom=atom, resid=mdres.index, resname=mdres.name)

            print(pseudotop)
            pseudotop.summary()
            pseudotop.angle_info()
            print(pseudotop("@CA").selected_indices())
            print(pseudotop[4])

            # try loading traj with pseudotop 
            traj = FrameArray()
            traj.top = pseudotop
            print('pseudotop: ', traj.top)

            traj.load("./data/md1_prod.Tc5b.x")
            traj0 = mdio.load("./data/md1_prod.Tc5b.x", "./data/Tc5b.top")
            for i in range(traj.size):
                assert_almost_equal(traj[i].coords, traj[i].coords)

if __name__ == "__main__":
    unittest.main()