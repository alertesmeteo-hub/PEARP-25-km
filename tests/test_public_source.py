import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from public_source import metadata

class MetadataTests(unittest.TestCase):
    def test_ensemble_product(self):
        h=bytearray(b'GRIB\x00\x00\x00\x02'+(1000).to_bytes(8,'big'))
        s=bytearray(37);s[:4]=(37).to_bytes(4,'big');s[4]=4;s[7:9]=(1).to_bytes(2,'big')
        s[17]=1;s[18:22]=(24).to_bytes(4,'big');s[22]=103;s[24:28]=(2).to_bytes(4,'big');s[35]=34;s[36]=35
        result=metadata(h+s)
        self.assertEqual(result['member'],34);self.assertEqual(result['ensemble_size'],35)
        self.assertEqual(result['level_value'],2);self.assertEqual(result['lead'],24)
    def test_bad_magic(self):
        with self.assertRaises(ValueError):metadata(b'not a grib file')
        with self.assertRaises(ValueError):metadata(b'')
    def test_statistical_ensemble_product(self):
        h=bytearray(b'GRIB\x00\x00\x00\x02'+(1000).to_bytes(8,'big'))
        s=bytearray(61);s[:4]=(61).to_bytes(4,'big');s[4]=4;s[7:9]=(11).to_bytes(2,'big')
        s[17]=1;s[18:22]=(21).to_bytes(4,'big');s[22]=103;s[24:28]=(10).to_bytes(4,'big');s[35]=34;s[36]=35
        s[44]=1;s[49]=2;s[51]=1;s[52:56]=(3).to_bytes(4,'big')
        result=metadata(h+s)
        self.assertEqual(result['range_length'],3);self.assertEqual(result['statistical_process'],2)
        self.assertEqual(result['member'],34)
        s[44]=2
        with self.assertRaises(ValueError):metadata(h+s)
