#!python3

import sys
import re

DEBUG = 0

#####
# Line class
##

class Line:

    def __init__(self, linenum, text):
        self.linenum = linenum
        self.addr = linenum
        self.text = text
        self.comment = None
        self.hard_addr = None

    def __str__(self):
        val = []
        if self.has_addr():
            val.append('%d:' % self.addr)
        if self.text:
            val.append(self.text)
        if self.comment:
            val.append('// %s' % self.comment)
        return ' '.join(val)

    def __repr__(self):
        val = []
        if self.has_addr():
            if not self.hard_addr is None:
                val.append('%d(%s):' % (self.addr, self.hard_addr))
            else:
                val.append('%d:' % self.addr)
        if self.text:
            val.append('"%s"' % self.text)
        if self.comment:
            val.append('// %s' % self.comment)
        return 'Line(%s)' % ' '.join(val)

    def has_addr(self):
        return not self.addr is None


#####
# Exceptions
##

class DuplicateLabelException(Exception):
    def __init__(self, label, line):
        super().__init__('\'@%s\', addr: %d' % (label, line.linenum))

class DuplicateDefineException(Exception):
    def __init__(self, label, line):
        super().__init__('\'@%s\', line: %d' % (label, line.linenum))

#####
# Helpers
##

processors = []

def fix_line_addresses(lines, settings):
    ip_inc = settings.get('ip_inc', 1)
    count = 0
    for line in lines:
        if line.has_addr():
            line.addr = count
            count += ip_inc
    return lines

def processor(func):
    def wrapper(lines, settings):
        lines = fix_line_addresses(lines, settings)
        return func(lines, settings)
    wrapper.__name__ = func.__name__
    processors.append(wrapper)
    return wrapper

#####
# Processors
##

@processor
def kept_comments(lines, _):
    for line in lines:
        if '//' in line.text:
            text, comment = line.text.split('//', 1)
            line.text = text.strip()
            line.comment = comment.strip()
            if not line.text:
                line.addr = None
    return lines

@processor
def strip_semicolons(lines, _):
    for line in lines:
        text = line.text.strip()
        if text.endswith(';'):
            line.text = text.rstrip(';').strip()
            if not line.text:
                line.addr = None
    return lines

@processor
def discarded_comments(lines, _):
    updated_lines = []
    for line in lines:
        if '#' in line.text:
            text = line.text.split('#')[0].strip()
            if text:  # exclude lines which were just a discarded comment
                line.text = text
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    return updated_lines

@processor
def hex_numbers(lines, _):
    def tohex(s):
        if s.startswith('0x'):
            try:
                return str(int(s, 16))
            except ValueError:
                pass
        return s
    p = re.compile('(0[xX][0-9a-fA-F]{2})')
    for line in lines:
        line.text = ''.join(map(tohex, p.split(line.text)))
    return lines

@processor
def defines(lines, _):
    defines = {}

    # find defines
    updated_lines = []
    for line in lines:
        if '=' in line.text:
            define, value = line.text.split('=', 1)
            define = define.strip().split(' ')[0]
            if define in defines:
                raise DuplicateDefineException(define, line)
            defines[define] = value.strip()
        else:
            updated_lines.append(line)

    # replace defines
    for line in updated_lines:
        for define, value in defines.items():
            line.text = line.text.replace('$' + define, value)

    return updated_lines

@processor
def constants(lines, _):
    constants = '''
    NOP JMP ATC MOV ACC UNC EQ ULT SLT ULE SLE PUR SHL SHR UAD SAD UMT SMT
    AND XOR OR NUM REG IND N8 N10 DINP GOUT DOUT FLAG DVAL SHFT OFLW SMPL
    '''.split()
    p = re.compile('(%s)' % '|'.join(constants))
    for line in lines:
        line.text = p.sub(r'`\1', line.text)
        while '``' in line.text:
            line.text = line.text.replace('``', '`')
    return lines

@processor
def keep_empty_lines(lines, _):
    for line in lines:
        if not line.text.strip() and not line.comment:
            line.text = ''
            line.addr = None
    return lines

@processor
def strip_starting_ending_empty_lines(lines, _):
    # strip empty lines at the start
    while len(lines):
        line = lines[0]
        if line.text.strip() or line.comment:
            break
        lines.pop(0)

    # and empty lines at the end
    while len(lines):
        line = lines[-1]
        if line.text.strip() or line.comment:
            break
        lines.pop()

    return lines

@processor
def hardcoded_addresses(lines, _):
    updated_lines = []
    prev_hard_addr = None
    for line in lines:
        # added hardcoded address if it was detected on the previous line
        if prev_hard_addr:
            line.hard_addr = prev_hard_addr
            line.addr = None
            prev_hard_addr = None
        else:
            text = line.text.strip()
            if text.startswith('[') and text.endswith(']:'):
                prev_hard_addr = text.split('[')[1].split(']:')[0].strip()
            else:
                updated_lines.append(line)
    return lines

@processor
def labels(lines, settings):
    labels = {}
    dot_labels = {}
    ip_inc = settings.get('ip_inc', 1)

    # find labels
    updated_lines = []
    offset = 0
    for line in lines:
        text = line.text.strip()
        if text.endswith(':'):
            label = text.split(':')[0].strip().split(' ')[0].strip()

            if label.startswith('.'):
                # dot labels can be redefined
                dot_labels[label.lstrip('.')] = line.addr - (offset * ip_inc)
            else:
                # normal labels can't
                if label in labels:
                    raise DuplicateLabelException(label, line)
                labels[label] = line.addr - (offset * ip_inc)
            offset += 1

            if line.comment:
                line.text = ''
                line.addr = None
                updated_lines.append(line)
        else:
            # replace dot labels
            for label, addr in dot_labels.items():
                line.text = line.text.replace('@' + label, str(addr))
            updated_lines.append(line)

    # replace normal labels
    for line in updated_lines:
        for label, addr in labels.items():
            line.text = line.text.replace('@' + label, str(addr))

    return updated_lines

@processor
def concatenated_bare_numbers(lines, _):
    def process(part):
        part = part.strip()
        if re.match('^-*\d+$', part):
            if part.startswith('-'):
                # deals with stupid --10 => --8'd10 cases
                *m, num = part.split('-')
                return '-'.join(m) + '-8\'d' + num
            else:
                return '8\'d' + part
        else:
            return part

    for line in lines:
        text = line.text.strip()
        if text.startswith('{') and text.endswith('}'):
            parts = map(process, text[1:-1].split(','))
            line.text = '{' + ', '.join(parts) + '}'
    return lines

@processor
def format_as_verilog(lines, _):
    for line in lines:
        if line.has_addr() or not line.hard_addr is None:
            line.text = '\t\t%s: data = %s;' % (
                    line.hard_addr or str(line.addr),
                    line.text.strip().rstrip(';'))
    return lines

@processor
def readd_comments(lines, _):
    for line in lines:
        if line.comment:
            if line.text:
                line.text = '%s // %s' % (line.text, line.comment)
            else:
                line.text = '\t\t// %s' % line.comment
    return lines


#####
# Compilation entry point
##

def compile(assembly, **settings):
    output = []
    output.append('always @(addr) begin')
    output.append('\tcase (addr)')

    # split assembly code into lines with line numbers
    lines = list(map(lambda a: Line(*a), enumerate(assembly.split('\n'))))

    # apply all processors
    if DEBUG:
        print('## original')
        list(map(print, map(repr, lines)))
    for proc in processors:
        lines = proc(lines, settings)
        if DEBUG:
            print('## ran processor:', proc.__name__)
            list(map(print, map(repr, lines)))

    # add lines to output
    for line in lines:
        output.append(line.text)

    output.append('')
    output.append('\t\tdefault: data = 35\'b0;')
    output.append('\tendcase')
    output.append('end')
    return '\n'.join(output)


#####
# Main entry point
##
def main():
    prog, *args = sys.argv

    if len(args) < 1:
        print('usage: %s PATH [IP_INC]' % prog)
        return

    ip_inc = 1
    if len(args) > 1:
        try:
            ip_inc = int(args[1])
        except ValueError:
            pass

    with open(args[0]) as fp:
        sys.stdout.write(compile(fp.read(), ip_inc=ip_inc))


if __name__ == '__main__':
    main()
