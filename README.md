# DSD-Project1-Assembler

Simple text transformation based assembler for the DSD project 1 instruction
set. Produces output that can be directly included in `ROM.v`.

## Usage

Make sure you use python 3.

```
py -3 compile.py all-inst-test.asm > all-inst-test.v
```

## Inclusion in the project

My preferred method is to use `` `include ``.

```
`include "CPU.vh"
module AsyncROM(input [7:0] addr, output reg [34:0] data);
    // directly include the output from the assembler
    `include "../../all-inst-test.v"

    // function definitions

    function [34:0] setBit;
        input [7:0] regNumber;
        input [2:0] flag;
        setBit = {`ACC, `OR, `REG, regNumber, `NUM, 8'b1 << flag, `N8};
    endfunction

    function [34:0] clearBit;
        input [7:0] regNumber;
        input [2:0] flag;
        clearBit = {`ACC, `AND, `REG, regNumber, `NUM, ~(8'b1 << flag), `N8};
    endfunction

endmodule
```

## License

The MIT License (MIT)

Copyright (c) 2016 Athir Saleem

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
