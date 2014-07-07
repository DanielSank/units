import sys
import os
import unittest
import fractions

frac = fractions.Fraction

sys.path.insert(0, os.path.abspath('..'))
from units import units

SD = units.SingleDimension

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


    def test_get_prefix(self):
        results = {'us': {'ch': 'u', 'val': -6, 'glyph': 's'},
                   'MHz': {'ch': 'M', 'val': 6, 'glyph': 'Hz'}
                   }
        for tag in results:
            ch, glyph = units.get_prefix(tag)
            val = units.SI_PREFIXES[ch]
            self.assertEqual(ch, results[tag]['ch'])
            self.assertEqual(val, results[tag]['val'])
            self.assertEqual(glyph, results[tag]['glyph'])


    def test_parse_one_dimensional_tag(self):
        tags = {'V': {'log10_pref': 0,
                    'glyph': 'V',
                    'pow': 1},
                'Hz': {'log10_pref': 0,
                    'glyph': 'Hz',
                    'pow': 1},
                'kHz^1/2': {'log10_pref': fractions.Fraction(3,2),
                    'glyph': 'Hz',
                    'pow': fractions.Fraction(1,2)}
        }
        for tag in tags:
            log10_pref, base_glyph, power = \
                units.parse_one_dimensional_tag(tag)
            self.assertEqual(log10_pref, tags[tag]['log10_pref'])
            self.assertEqual(base_glyph, tags[tag]['glyph'])
            self.assertEqual(power, tags[tag]['pow'])


    def test_numerator_denominator(self):
        tags = {'V': (['V'], []),
                'V/Hz^1/2': (['V'], ['Hz^1/2']),
                'km/ns^1/3': (['km'], ['ns^1/3'])
               }
        for tag in tags:
            num, denom = units.numerator_denominator(tag)
            num.sort()
            denom.sort()
            self.assertEqual(num, tags[tag][0])
            self.assertEqual(denom, tags[tag][1])


    def test_parse_tag(self):
        """
        Test tag parsing.
        
        'pot' means "power of ten".
        """
        tags = {'V': {'pot': 0,
                      'V': {'log10_pref': 0,
                            'glyph': 'V',
                            'power': frac(1)
                           }
                      },
                'V/Hz^1/2': {'pot': 0,
                             'V': {'log10_pref': 0,
                                   'glyph': 'V',
                                   'power': frac(1)
                                  },
                             'Hz': {'log10_pref': 0,
                                    'glyph': 'Hz',
                                    'power': frac(-1, 2)
                                   }
                            },
                'km^1/3': {'pot': 0,
                           'm': {'log10_pref': 1,
                                 'glyph': 'm',
                                 'power': frac(1, 3)
                                }
                          },
                'kHz/Hz^1/2': {'pot': 0,
                               'Hz': {'log10_pref': frac(3),
                                      'glyph': 'Hz',
                                      'power': frac(1, 2)
                                     }
                              },
                # All dimensions cancel, leaving only powers of ten.
                'kB/MB': {'pot': -3},
                'kY^1/2/Y^1/2': {'pot': frac(3, 2)},
                'MY^-3/2/Y^-3/2': {'pot': -9}
                }
        for tag in tags:
            parsed = units.parse_tag(tag)
            pot = tags[tag].pop('pot')
            self.assertEqual(parsed['log10_pref'], pot)
            for glyph in tags[tag]:
                expected = tags[tag][glyph]
                result = parsed[glyph]
                self.assertEqual(expected, result.as_dict())


    def test_multiplication(self):
        Hz = units.Unit('Hz')
        kHz = units.Unit('kHz')
        m = units.Unit('m')
        rtHz = units.Unit('Hz^1/2')
        pairs = [(m, Hz, units.Unit('m*Hz')),
                 (Hz, rtHz, units.Unit('Hz^3/2'))
                ]
        for x, y, result in pairs:
            self.assertEqual(x*y, result)


if __name__ == "__main__":
    unittest.main()
