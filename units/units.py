import fractions
import math
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
    A physical unit
    
    Construct a unit by passing a tag to its constructor, like this:
    >>> Unit('m/s')
    or
    >>> Unit('V/Hz^1/2')
    or
    >>> Unit('s*kg/ns')
    
    A Unit is essentially map from glyphs representing SI units to rational
    powers. Example glyphs are kHz, s, F, uK.
    
    Units can be multiplied together. They cannot be multiplied by scalars.
    Units can be raised to rational powers. Raising to float powers is
    supported by approximating the float with a rational number.
    """
    def __init__(self, data):
        if type(data) is str:
            self._map = parse_tag(data)
        else:
            msg = "Cannot initialize Unit with type %s"%type(data)
            raise TypeError(msg)
    
    # Dict-like interface
    
    def __iter__(self):
        return self._map.__iter__()
    
    def __contains__(self, key):
        return self._map.__contains__(key)
    
    def __getitem__(self, key):
        return self._map[key]
    
    def __setitem__(self, key, val):
        self._map[key] = val
    
    
    # Arithmetic
    
    def __mul__(self, other):
        if isinstance(other, Unit):
            result = self._mul_Unit(other)
            raise TypeError("Unit cannot multiply with type %s"%type(other))
        return result
    
    def _mul_Unit(self, other, factor=1):
        """Multiply by another Unit"""
        result = Unit('')
        processed_glyphs = set()
        # Handle other's glyphs
        for glyph in other:
            processed_glyphs.add(glyph)
            other_power = factor * other[glyph]
            if glyph in self:
                new_power = self[glyph] + other_power
            else:
                new_power = other_power
            result[glyph] = new_power
            if new_power == 0:
                result._map.pop(glyph)
        for glyph in self:
            if glyph in processed_glyphs:
                continue
            frac = self[glyph].numerator
            num, denom = frac.numerator, frac.denominator
            result[glyph] = fractions.Fraction(num, denom)
        return result
    
    def __div__(self, other):
        if isinstance(other, Unit):
            result = self._div_Unit(other)
        else:
            raise TypeError("Unit cannot divide with type %s"%type(other))
        return result
    
    def _div_Unit(self, other):
        return self._mul_Unit(other, factor=-1)
    
    def __pow__(self, pow):
        if isinstance(pow, int):
            result = self._pow_rational(pow)
        elif isinstance(pow, float):
            result = self._pow_float(pow)
        return result
    
    def _pow_rational(self, n):
        result = Unit('')
        for glyph in self:
            power = self[glyph] * n
            result[glyph] = power
        return result
    
    def _pow_float(self, f):
        # Turn f into a fraction
        integer_part = int(math.floor(f))
        fractional_part = f - integer_part
        denominator = int(1.0/fractional_part)
        approximation = integer_part + 1.0/denominator
        assert abs(approximation - f) < 1E-10
        power = integer_part + fractions.Fraction(1, denominator)
        return self._pow_rational(power)
    
    
    # Other
    
    def __str__(self):
        """Returns a human readable representation of the unit"""
        parts = []
        for glyph in self:
            power = self[glyph]
            if power == 1:
                parts.extend(['*', glyph])
            else:
                parts.extend(['*', glyph, '^', str(power)])
        return ''.join(parts[1:])


def parse_tag(tag):
    """
    Returns a map from glyph -> power
    
    Example:
    >>> result = parse_tag('V/Hz^1/2')
    >>> for key,val in result.items:
            print key,vale
    >>> V 1
    >>> Hz -1/2  
    """
    parsed = {}
    numerator, denominator = numerator_denominator(tag)
    for simple_tags, factor in zip((numerator, denominator), (1, -1)):
        for t in simple_tags:
            glyph, power = parse_one_dimensional_tag(t)
            power = power * factor
            power = power + parsed.get(glyph, 0)
            if power:
                parsed[glyph] = power
    return parsed


def numerator_denominator(tag):
    """
    Returns the numerator and denominator parts of a tag
    
    For example
    >>> numerator_denominator('s*m^2/Hz/K^3/4*L/s')
    >>> (['s', 'm^2', 'L'], ['Hz', 'K^3/4', s'])
    
    The order of the elements within the numerator and denominator lists is
    not specified.
    
    Note that a tag can appear both in the numerator and denominator.
    """
    numerator = []
    denominator = []
    for part in tag.split(MULT):
        # Split on division by another unit,
        # while ignoring division inside powers.
        pattern = re.compile("/(?=[^0-9])")
        slash_separated = re.split(pattern, part)
        # First item in a slash separted list goes in numerator,
        # while the rest go in denominator.
        if slash_separated[0] != '':
            numerator.append(slash_separated.pop(0))
            denominator.extend([den for den in slash_separated])
    return numerator, denominator


def parse_one_dimensional_tag(tag):
    """
    Returns (letter, power) for a single dimensional tag.
    
    A simple tag must have one of the following forms:
        [a-zA-Z]+
        [a-zA-Z]+^n
        [a-zA-Z]+^n/m
    
    Example:
    >>> parse_single_tag('K^3/4')
    >>> ('K', 3, 4)
    """
    # XXX check form of tag (ie using the regexp in the doc string)
    parts = tag.split('^')
    if len(parts) == 1:
        letter = parts[0]
        power = fractions.Fraction(1)
    elif len(parts) == 2:
        letter, exponent = parts
        power = fractions.Fraction(parts[1])
    return letter, power

