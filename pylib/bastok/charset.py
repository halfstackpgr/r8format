''' Generic character set support.

    This supports setting up translations between Unicode and native
    character sets that have exactly 256 code points, 0x00-0xFF.

    This does not handle encoding such as MSX's encoding of code point 0x05
    as b'\x01\x45'. Encoding/decoding should be done by the system-specific
    parsing routines.

'''

class Charset:
    ''' A mapping between a native character set, encoded as single
        bytes from 0x00 through 0xFF, and an arbitrary set of
        Unicode characters (1-character `str`s).
    '''

    def __init__(self, description, *maps):
        self.description = description
        self._nu = {}   # native (int) to Unicode (str) map
        self._un = {}   # Unicode (str) to native (int) map
        for m in maps: self.setchars(m)
        nlen = len(self._nu); ulen = len(self._un)
        if not (nlen == ulen == 0x100):
            raise RuntimeError(
                'Incomplete Charset: n=0x{:02X} ({}) u=0x{:02X} ({}) chars'
                .format(nlen, nlen, ulen, ulen))

    def _ncheck(self, n):
        ' Raise error if `n` is not a valid native char code. '
        if n < 0 or n > 0xFF:
            raise ValueError('Bad native char code {:02X}'.format(n))

    def _ucheck(self, u):
        ' Raise error if `u` is not a single Unicode character. '
        if not isinstance(u, str):
            raise ValueError('Unicode char not a str: {}'.format(repr(u)))
        if len(u) != 1:
            raise ValueError('str not length 1: {}'.format(repr(u)))

    def setchars(self, map):
        ''' Set character mappings in this Charset. `map` is a collection
            of pairs of (native character code, 1-char (unicode) string).

            This quietly overwrites existing values in order to make it
            easy to create custom charsets by modifying the standard ones.
        '''
        for n, u in map:
            self._ncheck(n); self._ucheck(u)
            #   When debugging you may uncomment this to help find duplicates.
            #if u in self._un: raise RuntimeError('Dup ' + repr(u))
            self._nu[n] = u
            self._un[u] = n

    def trans(self, n):
        ''' Return the translated version (a Unicode `str`) of native code
            point `n` (an `int` from 0x00 through 0xFF).

            Note that native points 0x00 through 0x1F are encoded as [0x01,
            0x40+`n`] in MSX BASIC; this takes the code point itself, not
            the encoded version of it.
        '''
        self._ncheck(n)
        return self._nu[n]

    def native(self, u):
        ''' Translate Unicode character `u`, a single-character `str`, to a
            `bytes` containing the MSX-BASIC encoding of that character.
            The result will be a single byte from 0x40 through 0xFF or two
            bytes, 0x01 followed by an "extended" character code from 0x40
            through 0x5F.
        '''
        self._ucheck(u)
        return bytes([self._un[u]])

####################################################################
#   Generic charsets for special purposes

class Unimplemented:
    ''' An unimplemented character set. This is useful to document the
        names of character sets whose translation has not yet been
        implemented.
    '''
    def __init__(self, name, description):
        self.name = name
        self.description = description + ' (not yet implemented)'
    def unimpl(self):
        raise NotImplementedError("charset '{}' ".format(self.name))
    def trans(self, n):     self.unimpl()
    def native(self, u):    self.unimpl()

class UTCharset:
    ''' A Charset converter for use by unit tests.

        This maps native codes 0x00 through 0xFF to Unicode code points
        U+F000 through U+F0FF, which are codes in the private use area
        (U+E000 - U+F8FF).

        This intentionally uses only non-ASCII codes on the Unicode side;
        that helps ensure that the CUT is using `str` where it should be.
    '''

    def trans(self, n):
        assert n >= 0 and n < 0x100, hex(n)
        return chr(0xF000+n)

    def native(self, u):
        assert len(u) == 1 and u >= chr(0xF000) and u < chr(0xF100), repr(u)
        return ord(u) - 0xF000


####################################################################
#   Utility functions

def chrsub(codechars, replacement):
    ''' Replace a code-character mapping in a list of such mappings.

        `codechars` is a sequence of (`int`,`str`) pairs, each a native
        code point and its associated Unicode character, and `replacement`
        a single pair to replace (at the same position) the pair in
        `codechars` with a matching code point. A new sequence with that
        code pont replaced is returned.

        A `LookupError` will be raised if the replacement code point
        is not found in `codechars`.

        This can be used to help build custom character set mappings
        provided to the `Charset` constructor.
    '''
    replaced = False
    ret = []
    for mapping in codechars:
        if mapping[0] == replacement[0]:
            ret.append(replacement)
            replaced = True
        else:
            ret.append(mapping)
    if not replaced:
        raise LookupError('code point {} not replaced'.format(replacement))
    return tuple(ret)
