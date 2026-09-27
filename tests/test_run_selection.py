import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_data import select_resources,STEPS

class RunSelectionTests(unittest.TestCase):
    def test_no_mixing_runs(self):
        resources=[{'title':f'pearp_glob025_202609270600_{h:02d}:00.grib'} for h in STEPS]
        resources.append({'title':'pearp_glob025_202609271200_00:00.grib'})
        run,selected=select_resources(resources)
        self.assertEqual(run,'2026092706')
        self.assertEqual(set(selected),set(STEPS))
    def test_incomplete_stops(self):
        with self.assertRaises(ValueError):select_resources([{'title':'pearp_glob025_202609270600_00:00.grib'}])
