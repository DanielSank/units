import fractions
import math
import re

SI_PREFIXES = { #prefix -> power of ten
    'G': 9,
    'M': 6,
    'k': 3,
    'c': -2,
    'm': -3,
    'u': -6,
    'n': -9,
    'p': -12,
    'a': -15
    }

POWERS_OF_TEN = {}
for key,value in SI_PREFIXES.items():
    POWERS_OF_TEN[value] = key

DERIVED_UNITS = {'Hz': 's^-1',
                 'N': 'kg*m/s^2'
                }


MULT = '*'


class SingleDimension(object):
    """
    A unit is a prefactor, glyph, and power: km^2
        prefactor: 10^3/2
        glyph: "m"
        power: 2
    We define the prefactor is such that the total unit is
    prefactor * (glyph ** power).
    
    A derived unit is a unit which is a combination of other units. For
    example, Hz is the same as 1/s. How should we keep track of this?
    We could just immediately convert Hz to 1/s whenever we encounter Hz.
    This isn't necessarily what we want though, because if we have a
    frequency chirp, we might want to express the chirp rate as a value in
    Hz/s. We'll also give units an equivalence
    Hz.equivalence = (0, "s", -1).
    """
    def __init__(self, glyph, power_of_ten, power):
        self.glyph = glyph
        self.power_of_ten = power_of_ten
        self.power = power
        self.equivalence = DERIVED_UNITS.get(glyph, None)
    
    def as_dict(self):
        d = {}
        d['log10_pref'] = self.power_of_ten
        d['power'] = self.power
        d['glyph'] = self.glyph
        return d
    
    def __repr__(self):
        return '<SingleDimension(%s, %s, %s)>'%(self.glyph, self.power_of_ten,
            self.power)


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
            d = parse_tag(data)
            self.powers_of_ten = d.pop('powers_of_ten')
            self._map = d
        else:
            msg = "Cannot initialize Unit with type %s"%type(data)
            raise TypeError(msg)
    
    # Dict-like interface
    
    def __iter__(self):
        return self._map.__iter__()
    
    def __contains__(self, key):
        return self._map.__contains__(key)
    
    def __getitem__(self, key):
        try:
            return self._map[key]
        except KeyError:
            return SingleDimension(key, 0, 0)
    
    def __setitem__(self, key, val):
        self._map[key] = val
    
    
    # Arithmetic
    
    def __mul__(self, other):
        if isinstance(other, Unit):
            result = self._mul_Unit(other)
        else:
            raise TypeError("Unit cannot multiply with type %s"%type(other))
        return result
    
    def _mul_Unit(self, other, factor=1):
        """Multiply by another Unit"""
        result = Unit('')
        processed_glyphs = set()
        # Handle other's glyphs
        for glyph in other:
            processed_glyphs.add(glyph)
            self_dim = self[glyph]
            other_dim = other[glyph]
            power = factor * other_dim.power + self_dim.power
            power_of_ten = factor * other_dim.power_of_ten + self_dim.power_of_ten
            if power == 0 and power_of_ten:
                result.power_of_ten += power_of_ten
            elif power:
                result[glyph] = SingleDimension(glyph, power_of_ten,
                                                power)
        # Handle our glyphs which haven't yet been processed
        for glyph in self:
            if glyph in processed_glyphs:
                continue
            dim = self[glyph]
            result[glyph] = SingleDimension(dim.glyph, dim.power_of_ten,
                dim.power)
        #Handle powers of ten
        result.powers_of_ten += self.powers_of_ten
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
        raise RuntimeError("This probably doesn't work")
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
        # Powers of ten which could not be written as prefixes
        extra_powers_of_ten = self.powers_of_ten
        for glyph in self:
            # Unpack data
            base_dimension = self[glyph]
            power_of_ten = base_dimension.power_of_ten
            power = base_dimension.power
            glyph = base_dimension.glyph
            # prefix
            if power_of_ten == 0:
                prefix = ''
            elif (power.denominator * power_of_ten).denominator == 1:
                prefix = POWERS_OF_TEN.get(power.denominator * power_of_ten, None)
                if prefix is None:
                    extra_powers_of_ten += power_of_ten
                    prefix = ''
            if power == 1:
                parts.extend(['*', prefix, glyph])
            else:
                parts.extend(['*', prefix, glyph, '^', str(power)])
        parts = parts[1:] #Drop leading '*'
        if extra_powers_of_ten:
            parts.insert(0, '10^%s '%(extra_powers_of_ten,))
        return ''.join(parts)


def parse_tag(tag):
    """
    Returns a map from glyph -> SingleDimension
    
    Example:
    >>> result = parse_tag('V/Hz^1/2')
    """
    parsed = {}
    all_tags = {}
    parsed['powers_of_ten']= 0
    numerator, denominator = numerator_denominator(tag)
    for simple_tags, factor in zip((numerator, denominator), (1, -1)):
        for t in simple_tags:
            power_of_ten, base_glyph, power = parse_one_dimensional_tag(t)
            # If this was in the denominator, change sign of the unit power
            # and the power of ten.
            power = power * factor
            power_of_ten = power_of_ten * factor
            all_tags.setdefault(base_glyph, []).append((power_of_ten, power))
    for base_glyph in all_tags:
        # Collect powers of ten and powers from each instance of each base
        # glyph.
        power_of_ten = sum([elem[0] for elem in all_tags[base_glyph]])
        power = sum([elem[1] for elem in all_tags[base_glyph]])
        # If the glyph's powers all cancelled, keep track of leftover powers of
        # ten.
        if power_of_ten and not power:
            parsed['powers_of_ten'] = parsed['powers_of_ten'] + power_of_ten
        # Otherwise, just make a SingleDimension to represent this glyph and its
        # associated powers of ten and powers.
        elif power:
            parsed[base_glyph] = SingleDimension(base_glyph,
                                    power_of_ten, power)
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
    Returns (power_of_ten, base_glyph, power) for a single dimensional tag.
    
    A simple tag must have one of the following forms:
        [a-zA-Z]+
        [a-zA-Z]+^n
        [a-zA-Z]+^n/m
    
    Example:
    >>> parse_single_tag('mHz^1/2')
    >>> (<-3/2>, 'Hz', <1/2>)
    """
    # XXX check form of tag (ie using the regexp in the doc string)
    parts = tag.split('^')
    if len(parts) == 1:
        prefix, base_glyph = get_prefix(parts[0])
        power = fractions.Fraction(1)
    elif len(parts) == 2:
        letters, exponent = parts
        prefix, base_glyph = get_prefix(letters)
        power = fractions.Fraction(exponent)
    else:
        raise RuntimeError("tag %s has too many ^"%(tag,))
    if prefix:
        power_of_ten = SI_PREFIXES[prefix] * power
    else:
        power_of_ten = 0
    return power_of_ten, base_glyph, power


def get_prefix(base_glyph):
    """
    Return the SI prefix and base glyph from a prefixed glyph.
    """
    prefix = ''
    n = 0
    if base_glyph=='m':
        return '', 'm'
    for p in SI_PREFIXES:
        if base_glyph.startswith(p):
            n = len(p)
            prefix = p
            break
    if n == len(base_glyph):
        raise RuntimeError("base_glyph %s is only a prefix"%(base_glyph,))
    return prefix, base_glyph[n:]
