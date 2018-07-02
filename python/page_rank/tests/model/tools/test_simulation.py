import unittest

import numpy as np

from page_rank.model.tools.utils import install_requirements
from page_rank.tests.model.tools.utils import SpiNNakerTestAdapter


class TestPageRankSimulation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        install_requirements()

    def test_integration(self):
        from page_rank.model.tools.simulation import PageRankSimulation

        # Graph specification
        iterations = 21
        run_time = iterations * .1  # time step
        edges = [
            ('A', 'B'),
            ('A', 'C'),
            ('B', 'D'),
            ('C', 'A'),
            ('C', 'B'),
            ('C', 'D'),
            ('D', 'C'),
        ]

        # SpiNNaker adapter
        expected_ranks = np.array([[0.13867, 0.35709, 0.19761, 0.30664]])
        adpt = SpiNNakerTestAdapter(ranks=expected_ranks)

        with PageRankSimulation(run_time, edges, spinnaker_adapter=adpt) as sim:
            self.assertTrue(sim.run(verify=True))


if __name__ == '__main__':
    unittest.main()