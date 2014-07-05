import fractions
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
    pass


def parse_tag(tag):
    """Returns a map from letter -> power"""
    parsed = {}
    numerator, denominator = numerator_denominator(tag)
    for simple_tags, factor in zip((numerator, denominator), (1, -1)):
        for t in simple_tags:
            letter, power = parse_one_dimensional_tag(t)
            power = power * factor
            existing_power = parsed.get(letter, 0)
            parsed[letter] = power + existing_power
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

