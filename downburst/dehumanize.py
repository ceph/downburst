import re


UNITS = dict(
    # nop, but nice to have explicitly
    B=1,

    # SI decimal prefixes
    kB=10**3,
    MB=10**6,
    GB=10**9,
    TB=10**12,
    PB=10**15,
    EB=10**18,
    ZB=10**21,
    YB=10**24,

    # IEC binary prefixes; kibibyte etc
    KiB=2**10,
    MiB=2**20,
    GiB=2**30,
    TiB=2**40,
    PiB=2**50,
    EiB=2**60,
    ZiB=2**70,
    YiB=2**80,

    # friendly aliases
    k=2**10,
    K=2**10,
    M=2**20,
    G=2**30,
    T=2**40,
    )


UNIT_RE = re.compile(r'^\s*(?P<num>[\d.]+)\s*(?P<unit>[a-zA-Z]+)?\s*$')


class NotANumberAndUnit(Exception):
    """
    Input does not look like a number with unit
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [repr(a) for a in self.args])


def parse(s):
    """
    Parse a human-friendly size into bytes.
    """
    if s is None:
        return s

    if isinstance(s, int):
        return s

    if isinstance(s, float):
        return int(round(s))

    match = UNIT_RE.match(s)
    if not match:
        raise NotANumberAndUnit(s)

    unit = match.group('unit')
    if unit is None:
        unit = 'B'
    try:
        multiplier = UNITS[unit]
    except KeyError:
        raise NotANumberAndUnit(s)

    num = match.group('num')
    try:
        num = int(num)
    except ValueError:
        num = float(num)
    num = num * multiplier
    num = int(round(num))
    return num
