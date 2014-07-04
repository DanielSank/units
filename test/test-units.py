import sys
import os
import unittest

sys.path.insert(0, os.path.abspath('..'))
from units import units

tags = {
    'm': (1,),
    's': (1,),
    'km': (3,)
    }

class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_multiplied_and_divided_tags(self):
        parse = units.multiplied_and_divided_tags
        s = 'Hz*m/s^3/4'
        mult, div = parse(s)
        self.assertEqual(set(mult), set(['Hz', 'm']))
        self.assertEqual(set(div), set(['s^3/4']))

if __name__ == "__main__":
    unittest.main()
