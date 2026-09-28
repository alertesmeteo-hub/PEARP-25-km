import sys
import unittest
from unittest.mock import Mock,patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from public_source import metadata,complete_catalog,HOST

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

class CatalogFallbackTests(unittest.TestCase):
    def test_listing_keeps_only_grib_files_in_requested_run(self):
        prefix='prod/data/arpege/glob025/202609271800/'
        filename='PEARP_202609271800_24:00.grib'
        xml=f'''<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <IsTruncated>false</IsTruncated>
          <Contents><Key>{prefix}{filename}</Key><Size>123456</Size></Contents>
          <Contents><Key>another-run/file.grib</Key><Size>1</Size></Contents>
          <Contents><Key>{prefix}notes.txt</Key><Size>1</Size></Contents>
        </ListBucketResult>'''
        response=Mock(content=xml.encode())
        with patch('public_source.requests.Session') as session:
            session.return_value.get.return_value=response
            result=complete_catalog([{'url':HOST+prefix+filename}])
            session.return_value.get.assert_called_once_with(HOST,params={'prefix':prefix,'max-keys':150},timeout=30)
        self.assertEqual(result,[{'title':filename,'url':HOST+prefix+filename,'filesize':123456}])

    def test_truncated_listing_is_rejected(self):
        response=Mock(content=b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated></ListBucketResult>')
        with patch('public_source.requests.Session') as session:
            session.return_value.get.return_value=response
            with self.assertRaises(ValueError):
                complete_catalog([{'url':HOST+'prod/data/arpege/glob025/202609271800/file.grib'}])
