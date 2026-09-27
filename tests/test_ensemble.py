import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ensemble import statistics,probability

class EnsembleTests(unittest.TestCase):
    def test_statistics(self):
        members={i:np.array([float(i)]) for i in range(35)}
        stats=statistics(members)
        self.assertEqual(stats['mean'][0],17)
        self.assertAlmostEqual(stats['p10'][0],3.4)
        self.assertAlmostEqual(stats['p90'][0],30.6)
        self.assertAlmostEqual(probability(members,34)[0],100/35)
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError):statistics({0:np.array([0.])})
    def test_missing_rejected(self):
        with self.assertRaises(ValueError):statistics({i:np.array([np.nan]) for i in range(35)})
