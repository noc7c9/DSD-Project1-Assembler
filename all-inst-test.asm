# Simple program that roughly checks the functionality of all instructions.
# The IP will get stuck at 0xFF (255) if all instructions work properly, if not
# IP *should* get stuck at another value.

#####
# JMPs, Jump Commands
##

// JMP UNC, Unconditional Jump
test_JMP_UNC:
	{JMP, UNC, N10, N10, @test_JMP_EQ}
	.fail:
		jmp(@fail) // JMP UNC failed
		# however stalling here won't work because jump isn't working xD

// JMP EQ, Jump on Equality
test_JMP_EQ:
	{JMP, EQ, NUM, 25, NUM, 50, @test_JMP_EQ}  # shouldn't jump
	{JMP, EQ, NUM, 25, NUM, 25, @test_JMP_ULT}
	.fail:
		jmp(@fail) // JMP EQ failed

// JMP ULT, Jump on Unsigned Less Than
test_JMP_ULT:
	{JMP, ULT, NUM, 25, NUM, 25, @test_JMP_ULT}  # shouldn't jump
	{JMP, ULT, NUM, 50, NUM, 25, @test_JMP_ULT}  # shouldn't jump
	{JMP, ULT, NUM, 10, NUM, 25, @test_JMP_SLT}
	.fail:
		jmp(@fail) // JMP ULT failed

// JMP SLT, Jump on Signed Less Than
test_JMP_SLT:
	{JMP, SLT, NUM, -5, NUM, -9, @test_JMP_SLT}  # shouldn't jump
	{JMP, SLT, NUM, 50, NUM, 25, @test_JMP_SLT}  # shouldn't jump
	{JMP, SLT, NUM, -5, NUM, -5, @test_JMP_SLT}  # shouldn't jump
	{JMP, SLT, NUM, -25, NUM, -10, @test_JMP_ULE}
	.fail:
		jmp(@fail) // JMP SLT failed

// JMP ULE, Jump on Unsigned Less Than or Equals
test_JMP_ULE:
	{JMP, ULE, NUM, 50, NUM, 25, @test_JMP_ULE}  # shouldn't jump
	{JMP, ULE, NUM, 10, NUM, 10, @test_JMP_SLE}
	.fail:
		jmp(@fail) // JMP ULE failed

// JMP SLE, Jump on Signed Less Than or Equals
test_JMP_SLE:
	{JMP, SLE, NUM, -5, NUM, -25, @test_JMP_SLE}  # shouldn't jump
	{JMP, SLE, NUM, -10, NUM, -10, @test_MOV_PUR}
	.fail:
		jmp(@fail) // JMP SLE failed


#####
# MOVs, Move Commands
##

// MOV PUR, Pure Move
test_MOV_PUR:
	{MOV, PUR, NUM, -25, REG, 0, N8}
	{JMP, EQ, REG, 0, NUM, -25, @test_MOV_SHL}
	.fail:
		jmp(@fail) // MOV PUR failed

// MOV SHL, Shift Left
test_MOV_SHL:
	{MOV, SHL, NUM, 2, REG, 0, N8}
	{JMP, EQ, REG, 0, NUM, 4, @test_MOV_SHR}
	.fail:
		jmp(@fail) // MOV SHL failed

// MOV SHR, Shift Right
test_MOV_SHR:
	{MOV, SHR, NUM, 4, REG, 0, N8}
	{JMP, EQ, REG, 0, NUM, 2, @test_ACC_UAD}
	.fail:
		jmp(@fail) // MOV SHR failed


#####
# ACCs, Accumulate Commands
##

// ACC UAD, Unsigned Addition
test_ACC_UAD:
	{MOV, PUR, NUM, 100, REG, 0, N8}
	{ACC, UAD, REG, 0, NUM, 100, N8}
	{JMP, EQ, REG, 0, NUM, 200, @test_ACC_SAD}
	.fail:
		jmp(@fail) // ACC UAD failed

// ACC SAD, Signed Addition
test_ACC_SAD:
	{MOV, PUR, NUM, -50, REG, 0, N8}
	{ACC, SAD, REG, 0, NUM, 75, N8}
	{JMP, EQ, REG, 0, NUM, 25, @test_ACC_UMT}
	.fail:
		jmp(@fail) // ACC SAD failed

// ACC UMT, Unsigned Multiplication
test_ACC_UMT:
	{MOV, PUR, NUM, 100, REG, 0, N8}
	{ACC, UMT, REG, 0, NUM, 2, N8}
	{JMP, EQ, REG, 0, NUM, 200, @test_ACC_SMT}
	.fail:
		jmp(@fail) // ACC UMT failed

// ACC SMT, Signed Multiplication
test_ACC_SMT:
	{MOV, PUR, NUM, 25, REG, 0, N8}
	{ACC, SMT, REG, 0, NUM, -2, N8}
	{JMP, EQ, REG, 0, NUM, -50, @test_ACC_AND}
	.fail:
		jmp(@fail) // ACC SMT failed

// ACC AND, Bitwise And
test_ACC_AND:
	{MOV, PUR, NUM, 8'b1111_1111, REG, 0, N8}
	{ACC, AND, REG, 0, NUM, 8'b0010_1001, N8}
	{JMP, EQ, REG, 0, NUM, 8'b0010_1001, @test_ACC_OR}
	.fail:
		jmp(@fail) // ACC OR failed

// ACC OR, Bitwise Or
test_ACC_OR:
	{MOV, PUR, NUM, 8'b1100_1101, REG, 0, N8}
	{ACC, OR, REG, 0, NUM, 8'b1011_1011, N8}
	{JMP, EQ, REG, 0, NUM, 8'b1111_1111, @test_ACC_XOR}
	.fail:
		jmp(@fail) // ACC OR failed

// ACC XOR, Bitwise XOR
test_ACC_XOR:
	{MOV, PUR, NUM, 8'b1100_1101, REG, 0, N8}
	{ACC, XOR, REG, 0, NUM, 8'b1011_1011, N8}
	{JMP, EQ, REG, 0, NUM, 8'b0111_0110, @test_ATC_SHFT}
	.fail:
		jmp(@fail) // ACC XOR failed


#####
# ATCs, Atomic Test and Clear Commands
##

// ATC SHFT, Shift Register
test_ATC_SHFT:
	{MOV, PUR, NUM, 0, REG, FLAG, N8} # reset flag register
	{MOV, SHR, NUM, 1, REG, 0, N8}
	{ATC, SHFT, N10, N10, @test_ATC_OFLW}
	.fail:
		jmp(@fail) // ATC SHFT failed

// ATC OFLW, Overflow Register
test_ATC_OFLW:
	{MOV, PUR, NUM, 0, REG, FLAG, N8} # reset flag register
	{MOV, PUR, NUM, 200, REG, 0, N8}
	{ACC, UAD, REG, 0, NUM, 200, N8}
	{ATC, OFLW, N10, N10, 0xFF}
	.fail:
		jmp(@fail) // ATC SHFT failed


#####
# Success, display FF on IP display
##

// Success
[0xFF]:
	jmp(0xFF)
