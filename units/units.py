import re

SI_POWERS = { #prefix -> power of ten
    'k': 3,
    'M': 6,
    'G': 9,
    'c': -2,
    'm': -3
    }

MULT = '*'

class Unit(object):
    """
    A physical unit.
    
    Basically a set of basic units with powers.
    """
    def __init__(self, tag):
        d = self.parse_tag(tag)
        self._data = d
    
    @staticmethod
    def parse_tag(tag):
        """Returns a map from unit->power"""
        multiplied_tags = tag.split(MULT)
        divided_tags = []
        for multiplied_tag in multiplied_tags:
            # Find each division by another unit
            # while ignoring division in powers.
            pattern = re.compile(r"/[^0-9]") #Divide by not a number
            matches = re.finditer(pattern, multiplied_tag)
            for m in matches:
                start, end = m.span()
                divided_tags.append(multiplied_tag[start+1:end])
        return multiplied_tags, divided_tags
    
    def __str__(self):
        pass

def powers(s):
    """Returns positive and negative parts of a rational power"""
    if '/' in s:
        pos, neg = (int(n) for n in s.split('/'))
        if pos == 1:
            pos = 0
    else:
        pos, neg = (int(s), 0)
    return pos, neg

def numerator_denominator(tag):
    """Returns the numerator and denominator parts of a tag"""
    numerator = []
    denominator = []
    for part in tag.split(MULT):
        # Split on division by another unit,
        # while ignoring division inside powers.
        pattern = re.compile("/(?=[^0-9])")
        slash_separated = re.split(pattern, part)
        # First item in a slash separted list goes in numerator,
        # while the rest go in denominator.
        numerator.append(slash_separated.pop(0))
        denominator.extend([den for den in slash_separated])
    return numerator, denominator

