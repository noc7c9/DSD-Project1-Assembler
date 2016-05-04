#!python3

import pytest
from itertools import zip_longest

from compile import compile, DuplicateLabelException, DuplicateDefineException


#####
# Helpers
###

skip = pytest.mark.skip()

def find_max_width(text):
    __tracebackhide__ = True
    max_width = 0
    for line in text.split('\n'):
        max_width = max(len(line), max_width)
    return max_width

def pad_text(text, width):
    __tracebackhide__ = True
    padded = []
    for line in text.split('\n'):
        padded.append(line.ljust(width))
    return '\n'.join(padded)

def print_as_columns(a, b):
    __tracebackhide__ = True
    padwidth = find_max_width(a)
    a = pad_text(a, padwidth)
    padding = ' ' * padwidth
    columns = list(zip_longest(a.split('\n'), b.split('\n'),
        fillvalue=padding))
    template = '%' + str(len(str(len(columns)))) + 'd:   %s | %s'
    for i, (la, lb) in enumerate(columns):
        print(template % (i, la, lb))

def compile_and_compare(assembly, expected_machine_code, **compiler_args):
    __tracebackhide__ = True

    recieved_machine_code = compile(assembly, **compiler_args).strip('\n').replace('\t', '    ').rstrip()
    expected_machine_code = expected_machine_code.strip('\n').replace('\t', '    ').rstrip()

    print_as_columns(
            'RECEIVED\n' + recieved_machine_code,
            'EXPECTED\n' + expected_machine_code)

    recieved_machine_code = recieved_machine_code.strip().split('\n')
    expected_machine_code = expected_machine_code.strip().split('\n')

    lines = zip_longest(recieved_machine_code, expected_machine_code, fillvalue='')
    for i, (r_line, e_line) in enumerate(lines):
        r_line = r_line.strip()
        e_line = e_line.strip()
        # print('%03d: \'%s\'' % (i, assembly[i].strip()))
        assert(r_line == e_line)


#####
# Tests
###

def test_blank():
    compile_and_compare('''
    ''', '''
    always @(addr) begin
        case (addr)

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_basic():
    compile_and_compare('''
    35'b0010_000_00_10001000_01_00011110_00000000
    {`MOV, `PUR, `NUM, 8'd 7, `REG, `DOUT, `N8};
    {MOV, PUR, NUM, 8'd 7, REG, DOUT, N8};
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = 35'b0010_000_00_10001000_01_00011110_00000000;
            1: data = {`MOV, `PUR, `NUM, 8'd 7, `REG, `DOUT, `N8};
            2: data = {`MOV, `PUR, `NUM, 8'd 7, `REG, `DOUT, `N8};

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_comments():
    compile_and_compare('''
    // in the final output
    35'b0010_000_00_10001000_01_00011110_00000000
    # not in the final output
    ''', '''
    always @(addr) begin
        case (addr)
            // in the final output
            0: data = 35'b0010_000_00_10001000_01_00011110_00000000;

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_same_line_comments():
    compile_and_compare('''
    labela: # discarded
        abc // kept
    labelb: // kept
        abc # discarded
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = abc; // kept
            // kept
            1: data = abc;

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_constants():
    compile_and_compare('''
    mov(DINP, GOUT)
    setBit(GOUT, DVAL)
    mov(DINP, DOUT)
    jmp(0)

    NOP JMP ATC MOV ACC UNC EQ ULT SLT ULE SLE PUR
    SHL SHR UAD SAD UMT SMT AND XOR OR NUM REG IND
    N8 N10 DINP GOUT DOUT FLAG DVAL SHFT OFLW SMPL
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = mov(`DINP, `GOUT);
            1: data = setBit(`GOUT, `DVAL);
            2: data = mov(`DINP, `DOUT);
            3: data = jmp(0);

            4: data = `NOP `JMP `ATC `MOV `ACC `UNC `EQ `ULT `SLT `ULE `SLE `PUR;
            5: data = `SHL `SHR `UAD `SAD `UMT `SMT `AND `XOR `OR `NUM `REG `IND;
            6: data = `N8 `N10 `DINP `GOUT `DOUT `FLAG `DVAL `SHFT `OFLW `SMPL;

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_bare_numbers_in_concat():
    compile_and_compare('''
    define = 123
    label:
        set(0, 123) # untouched
    {a, 123, b} # will be given a size
    {a, -10, b} # negative numbers handled properly
    {a, --10, b} # tricky
    {a, 8'b10, b} # ignored
    {a, 8'h10, b} # ignored
    {a, a10b, b} # ignored
    {a, $define, b} # handled
    {a, @label, b} # handled
    {8'b1, 4};
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = set(0, 123);
            1: data = {a, 8'd123, b};
            2: data = {a, -8'd10, b};
            3: data = {a, --8'd10, b};
            4: data = {a, 8'b10, b};
            5: data = {a, 8'h10, b};
            6: data = {a, a10b, b};
            7: data = {a, 8'd123, b};
            8: data = {a, 8'd0, b};
            9: data = {8'b1, 8'd4};

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_hex_numbers():
    compile_and_compare('''
    // this is untouched 0x3d
    [0xff]: // 0xaA
        jmp(0xFF)
    jmp(0xFg)
    fake(0xaa, 0xbb)
    ''', '''
    always @(addr) begin
        case (addr)
            // this is untouched 0x3d
            // 0xaA
            255: data = jmp(255);
            0: data = jmp(0xFg);
            1: data = fake(170, 187);

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_labels():
    compile_and_compare('''
    mov(DINP, GOUT)

    here:
        setBit(GOUT, DVAL)
        mov(DINP, DOUT)
        jmp(@here)
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = mov(`DINP, `GOUT);

            1: data = setBit(`GOUT, `DVAL);
            2: data = mov(`DINP, `DOUT);
            3: data = jmp(1);

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_dot_labels():
    compile_and_compare('''
    .outer_loop:
        35'b0
        .inner_loop:
            35'b0
            jmp(@inner_loop)
        jmp(@outer_loop)

    .outer_loop:
        35'b0
        .inner_loop:
            35'b0
            jmp(@inner_loop)
        jmp(@outer_loop)

    .outer_loop:
        35'b0
        .middle_loop:
            35'b0
            .inner_loop:
                35'b0
                jmp(@inner_loop)
            jmp(@middle_loop)
        jmp(@outer_loop)
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = 35'b0;
            1: data = 35'b0;
            2: data = jmp(1);
            3: data = jmp(0);

            4: data = 35'b0;
            5: data = 35'b0;
            6: data = jmp(5);
            7: data = jmp(4);

            8: data = 35'b0;
            9: data = 35'b0;
            10: data = 35'b0;
            11: data = jmp(10);
            12: data = jmp(9);
            13: data = jmp(8);

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_duplicate_labels():
    with pytest.raises(DuplicateLabelException):
        compile('''
        here   :
            a
        another:
            b
          here :
            c
        ''')

def test_defines():
    compile_and_compare('''
    target = GOUT
    mov(DINP, $target)
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = mov(`DINP, `GOUT);

            default: data = 35\'b0;
        endcase
    end
    ''')

def test_duplicate_defines():
    with pytest.raises(DuplicateDefineException):
        compile('''
        a = 123
        a = 123
        ''')

def test_ip_inc():
    compile_and_compare('''
        mov(DINP, GOUT)
    here:
        setBit(GOUT, DVAL)
        mov(DINP, DOUT)
        jmp(@here)
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = mov(`DINP, `GOUT);
            4: data = setBit(`GOUT, `DVAL);
            8: data = mov(`DINP, `DOUT);
            12: data = jmp(4);

            default: data = 35\'b0;
        endcase
    end
    ''', ip_inc=4)

def test_hardcoded_addresses():
    compile_and_compare('''
    [123]:
        test

    m2mul_init:
        set(DOUT, 1)
    loop1:
        acc(SMT, DOUT, -2)
    jmpback:
        atc(OFLW, @plus1_init)
        jmp(@loop1)

    plus1_init:
        set(DOUT, 250)
    loop2:
        acc(UAD, DOUT, 1)
        atc(OFLW, @jmpback)
        jmp(@loop2)

    [1, 5, 9, 13, 17, 21, 25]:
        mov(FLAG, GOUT)
    [2, 6, 10, 14, 18, 22, 26]:
        setBit(`GOUT, `DVAL);
    ''', '''
    always @(addr) begin
        case (addr)
            123: data = test;

            0: data = set(`DOUT, 1);
            4: data = acc(`SMT, `DOUT, -2);
            8: data = atc(`OFLW, 16);
            12: data = jmp(4);

            16: data = set(`DOUT, 250);
            20: data = acc(`UAD, `DOUT, 1);
            24: data = atc(`OFLW, 8);
            28: data = jmp(20);

            1, 5, 9, 13, 17, 21, 25: data = mov(`FLAG, `GOUT);
            2, 6, 10, 14, 18, 22, 26: data = setBit(`GOUT, `DVAL);

            default: data = 35\'b0;
        endcase
    end
    ''', ip_inc=4)

def test_complex_example():
    compile_and_compare('''
    # defines
    PLUS1_INITIAL_VALUE = 250

    init:
        set(DOUT, 1)

    // even supports comments!
    loop_minus2mul:
        acc(SMT, DOUT, -2)
    restart_minus2:
        atc(OFLW, @block_plus1)
        jmp(@loop_minus2mul)

    block_plus1: # test
        set(DOUT, $PLUS1_INITIAL_VALUE) // they can be on a line with code
    loop_plus1:
        acc(UAD, DOUT, 1)               # can be excluded from output as well via #
        atc(OFLW, @restart_minus2)
        jmp(@loop_plus1)
    ''', '''
    always @(addr) begin
        case (addr)
            0: data = set(`DOUT, 1);

            // even supports comments!
            4: data = acc(`SMT, `DOUT, -2);
            8: data = atc(`OFLW, 16);
            12: data = jmp(4);

            16: data = set(`DOUT, 250); // they can be on a line with code
            20: data = acc(`UAD, `DOUT, 1);
            24: data = atc(`OFLW, 8);
            28: data = jmp(20);

            default: data = 35\'b0;
        endcase
    end
    ''', ip_inc=4)

def test_mixed_label_types():
    compile_and_compare('''
    // JMP UNC, Unconditional Jump
    test_JMP_UNC:
        jmp(@test_JMP_EQ) # jump to next test
        .fail:
            jmp(@fail) // JMP UNC failed
            # however stalling here won't work because jump fails xD

    // JMP EQ, Jump on Equality
    test_JMP_EQ:
        {JMP, EQ, NUM, 25, NUM, 25, @test_JMP_UNC}
        .fail:
            jmp(@fail) // JMP EQ failed
    ''', '''
    always @(addr) begin
        case (addr)
            // JMP UNC, Unconditional Jump
            0: data = jmp(2);
            1: data = jmp(1); // JMP UNC failed

            // JMP EQ, Jump on Equality
            2: data = {`JMP, `EQ, `NUM, 8'd25, `NUM, 8'd25, 8'd0};
            3: data = jmp(3); // JMP EQ failed

            default: data = 35\'b0;
        endcase
    end
    ''')
