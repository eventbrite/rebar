import re
import manuel
import textwrap

from manuel.codeblock import (
    CodeBlock,
    execute_code_block,
)

TESTCODEBLOCK_START = re.compile(
    r'(^\.\.\s*testcode::(?:\s*\:\w+\:.*\n)*)',
    re.MULTILINE)
TESTCODEBLOCK_END = re.compile(r'(\n\Z|\n(?=\S))')


def find_code_blocks(document):
    for region in document.find_regions(
            TESTCODEBLOCK_START,
            TESTCODEBLOCK_END):
        start_end = TESTCODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])
        source_location = '%s:%d' % (document.location, region.lineno)
        code = compile(source, source_location, 'exec', 0, True)
        document.claim_region(region)
        region.parsed = CodeBlock(code, source)


class Manuel(manuel.Manuel):
    def __init__(self):
        manuel.Manuel.__init__(self, [find_code_blocks], [execute_code_block])
