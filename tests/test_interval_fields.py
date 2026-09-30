import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from interval_fields import matching_interval,validate_interval,precipitation_total,gust_speed
from ensemble import statistics

class IntervalTests(unittest.TestCase):
    def test_gust_requires_three_hours(self):
        r={'template':11,'statistical_process':2,'range_unit':1,'range_length':3,'lead':21}
        self.assertTrue(matching_interval(r,'gust_u',24))
        r.update(range_length=1,lead=23)
        self.assertFalse(matching_interval(r,'gust_u',24))
        self.assertFalse(matching_interval(r,'gust_u',0))
    def test_gust_uses_one_hour_at_first_two_steps(self):
        self.assertTrue(matching_interval({'template':11,'statistical_process':2,'range_unit':1,'range_length':1,'lead':0},'gust_u',1))
        self.assertTrue(matching_interval({'template':11,'statistical_process':2,'range_unit':1,'range_length':1,'lead':1},'gust_u',2))
        self.assertFalse(matching_interval({'template':11,'statistical_process':2,'range_unit':1,'range_length':2,'lead':0},'gust_u',2))
    def test_accumulation_not_rate(self):
        values=precipitation_total([np.array([1.]),np.array([2.]),np.array([3.]),np.array([4.])])
        self.assertEqual(values[0],10.)
        r={'template':11,'statistical_process':1,'range_unit':1,'range_length':24,'lead':0}
        self.assertTrue(matching_interval(r,'rain_conv',24))
        r['lead']=21
        self.assertFalse(matching_interval(r,'rain_conv',24))
    def test_gust_vector_norm_before_ensemble(self):
        self.assertEqual(gust_speed(np.array([-3.]),np.array([4.]))[0],18.)
        members={i:gust_speed(np.array([3. if i%2 else -3.]),np.array([4.])) for i in range(35)}
        self.assertEqual(statistics(members)['mean'][0],18.)
    def test_invalid_precipitation_rejected(self):
        with self.assertRaises(ValueError):precipitation_total([np.array([-1.])]*4)
        with self.assertRaises(ValueError):precipitation_total([np.array([np.nan])]*4)
    def test_period_validation(self):
        values={'productDefinitionTemplateNumber':11,'typeOfStatisticalProcessing':2,'startStep':21,'endStep':24,'indicatorOfUnitForTimeRange':1,'lengthOfTimeRange':3,'stepType':'max','units':'m s**-1'}
        validate_interval(values,lambda h,k:h[k],'gust_u',24)
        values['endStep']=48
        with self.assertRaises(ValueError):validate_interval(values,lambda h,k:h[k],'gust_u',24)
        early={'productDefinitionTemplateNumber':11,'typeOfStatisticalProcessing':2,'startStep':0,'endStep':1,'indicatorOfUnitForTimeRange':1,'lengthOfTimeRange':1,'stepType':'max','units':'m s**-1'}
        validate_interval(early,lambda h,k:h[k],'gust_u',1)
        early.update(startStep=1,endStep=2)
        validate_interval(early,lambda h,k:h[k],'gust_u',2)
