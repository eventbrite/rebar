import doctest
import re
import sys


UNICODE_RE = re.compile(r'(u)(\'|"|""")')
UNICODE_REPL = r'\2'


class PermissiveUnicodeDocTestParser(doctest.DocTestParser):

    def _parse_example(self, m, name, lineno):

        (source, options, want, exc_msg,) = \
            doctest.DocTestParser._parse_example(
                self, m, name, lineno,
            )

        if sys.version_info >= (3,):
            # strip ``u`` from output strings
            want = UNICODE_RE.sub(UNICODE_REPL, want)

        return (source, options, want, exc_msg)
