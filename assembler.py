#! /usr/bin/env python3

import re
import os
import sys
import optparse

symbols = {}

instructions = []

relocations = []


class AssemblerError(Exception):
    pass


class AssemblerSyntaxError(AssemblerError):
    def __init__(self, line, reason):
        self.line = line
        self.reason = reason

    def __str__(self):
        return "Syntax error on line %d: %s" % (self.line, self.reason)


class AssemblerRangeError(AssemblerError):
    def __init__(self, line, reason):
        self.line = line
        self.reason = reason

    def __str__(self):
        return "Range error on line %d: %s" % (self.line, self.reason)


label_re = re.compile(r"""^(?P<labels>.*:)?(?P<gunk>[^:]*)$""")
comment_re = re.compile(r"""^(?P<important>[^#]*)(?P<comment>#.*)?$""")
valid_label_re = re.compile(r"""^\w+$""")

rtype_0_re = re.compile(r"""^(?P<instr>(nop|halt))""")
rtype_1_re = re.compile(
    r"""^(?P<instr>(pop|push|jr|mfhi|mflo|tty|rnd|kbd))\s+(?P<r>r([0-9]|[1-2][0-9]|30|31))$"""
)
rtype_2_re = re.compile(
    r"""^(?P<instr>(mult|mulu|div|divu))\s+(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s+(?P<rt>r([0-9]|[1-2][0-9]|30|31))$"""
)
rtype_3_re = re.compile(
    r"""^(?P<instr>(add|sub|slt|sltu|and|or|nor|xor))\s+(?P<rd>r([0-9]|[1-2][0-9]|30|31))\s+(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s+(?P<rt>r([0-9]|[1-2][0-9]|30|31))$"""
)

itype_1_re = re.compile(
    r"""^(?P<instr>(blez|bgtz|bltz))\s+(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s+(?P<label>\w+)$"""
)
itype_2_re = re.compile(
    r"""^(?P<instr>(addi|slti|sltiu|andi|ori|xori))\s+(?P<rt>r([0-9]|[1-2][0-9]|30|31))\s+(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s+(?P<immed>-?(0x)?[0-9a-fA-F]+)$"""
)
branch_re = re.compile(
    r"""^(?P<instr>(beq|bne))\s+(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s+(?P<rt>r([0-9]|[1-2][0-9]|30|31))\s+(?P<label>\w+)$"""
)

mem_re = re.compile(
    r"""^(?P<instr>(lw|sw))\s+(?P<rt>r([0-9]|[1-2][0-9]|30|31))\s+(?P<immed>-?(0x)?[0-9a-fA-F]+)\s*\(\s*(?P<rs>r([0-9]|[1-2][0-9]|30|31))\s*\)$"""
)

jtype_re = re.compile(r"""^(?P<instr>(j))\s+(?P<label>\w+)$""")

opcodes = {
    "nop": int("000000", 2),
    "add": int("000000", 2),
    "sub": int("000000", 2),
    "mult": int("000000", 2),
    "mulu": int("000000", 2),
    "div": int("000000", 2),
    "divu": int("000000", 2),
    "slt": int("000000", 2),
    "sltu": int("000000", 2),
    "and": int("000000", 2),
    "or": int("000000", 2),
    "nor": int("000000", 2),
    "xor": int("000000", 2),
    "addi": int("001000", 2),
    "slti": int("001010", 2),
    "sltiu": int("001011", 2),
    "andi": int("001100", 2),
    "ori": int("001101", 2),
    "xori": int("001110", 2),
    "lw": int("100011", 2),
    "sw": int("101011", 2),
    "pop": int("111000", 2),
    "push": int("111000", 2),
    "beq": int("000100", 2),
    "bne": int("000101", 2),
    "blez": int("000110", 2),
    "bgtz": int("000111", 2),
    "bltz": int("000001", 2),
    "j": int("000010", 2),
    "jr": int("000000", 2),
    "mfhi": int("000000", 2),
    "mflo": int("000000", 2),
    "halt": int("111111", 2),
    "tty": int("111111", 2),
    "rnd": int("111111", 2),
    "kbd": int("111111", 2),
}

functs = {
    "nop": int("000000", 2),
    "add": int("100000", 2),
    "sub": int("100010", 2),
    "mult": int("011000", 2),
    "mulu": int("011001", 2),
    "div": int("011010", 2),
    "divu": int("011011", 2),
    "slt": int("101010", 2),
    "sltu": int("101011", 2),
    "and": int("100100", 2),
    "or": int("100101", 2),
    "nor": int("100111", 2),
    "xor": int("101000", 2),
    "pop": int("000000", 2),
    "push": int("000001", 2),
    "jr": int("001000", 2),
    "mfhi": int("010000", 2),
    "mflo": int("010010", 2),
    "halt": int("111111", 2),
    "tty": int("000001", 2),
    "rnd": int("000010", 2),
    "kbd": int("000100", 2),
}


def validLabel(s):
    return valid_label_re.match(s) != None


def fill_symbol_table(inputFile):
    lineNo = 1
    instructionsSeen = 0
    for line in inputFile:
        # strip any comments
        match = comment_re.match(line)

        if not match:
            raise AssemblerSyntaxError(lineNo, "Unable to parse line: %s" % line)

        line = match.group("important")

        line = line.strip()

        match = label_re.match(line)

        if not match:
            raise AssemblerSyntaxError(lineNo, "Unable to parse line: %s" % line)

        labels_string = match.group("labels")

        if labels_string:
            labels = labels_string[:-1].split(":")
        else:
            labels = []

        for label in labels:
            if not validLabel(label):
                raise AssemblerSyntaxError(lineNo, "Invalid label: '%s'" % label)
            if label in symbols:
                raise AssemblerSyntaxError(lineNo, "Label %s already defined" % label)
            symbols[label] = instructionsSeen

        instruction = match.group("gunk").replace(",", " ").strip()
        if len(instruction) != 0:
            # there's an instruction here, so increment the number of instructions
            instructionsSeen += 1
        lineNo += 1


def imm_check(signed, both_allowed, immediate, lineNo):
    if both_allowed:
        if immediate > 2**16 - 1 or immediate < -(2**15):
            raise AssemblerSyntaxError(lineNo, "immediate out of range")
    else:
        if signed and (immediate > 2**15 - 1 or immediate < -(2**15)):
            raise AssemblerSyntaxError(lineNo, "signed immediate out of range")
        if (not signed) and (immediate > 2**16 - 1 or immediate < 0):
            raise AssemblerSyntaxError(lineNo, "unsigned immediate out of range")


def pprintInstr(separators, num):
    binary = "{0:032b}".format(num)
    for i, sep in enumerate(separators):
        binary = "|".join([binary[: sep + i], binary[sep + i :]])
    return binary


def assemble_instructions(inputFile):
    lineNo = 1
    instructionsSeen = 0
    instructions = []
    for line in inputFile:
        # strip any comments
        match = comment_re.match(line)
        assert match
        line = match.group("important")

        line = line.strip()

        match = label_re.match(line)

        instruction = match.group("gunk").lower().replace(",", " ").strip()

        rtype_0 = rtype_0_re.match(instruction)
        rtype_1 = rtype_1_re.match(instruction)
        rtype_2 = rtype_2_re.match(instruction)
        rtype_3 = rtype_3_re.match(instruction)

        itype_1 = itype_1_re.match(instruction)
        itype_2 = itype_2_re.match(instruction)
        branch = branch_re.match(instruction)

        mem = mem_re.match(instruction)
        jtype = jtype_re.match(instruction)

        if len(instruction) != 0:
            num = 0

            if rtype_0:
                instr = rtype_0.group("instr")
                funct = functs[instr]
                opcode = opcodes[instr]
                rd, rs, rt = 0, 0, 0
                num = opcode << 26 | rs << 21 | rt << 16 | rd << 11 | funct
                debug(
                    "{0:s} hex_code: {2:04x}\n{1:s}\n".format(
                        instruction, pprintInstr([6, 11, 16, 21, 26], num), num
                    )
                )
            elif rtype_1:
                instr = rtype_1.group("instr")
                funct = functs[instr]
                opcode = opcodes[instr]
                rd, rs, rt = 0, 0, 0
                if instr in ["pop", "mfhi", "mflo", "rnd", "kbd"]:
                    rd = int(rtype_1.group("r")[1:])
                else:
                    rs = int(rtype_1.group("r")[1:])
                num = opcode << 26 | rs << 21 | rt << 16 | rd << 11 | funct
                debug(
                    "{0:s} rtype: rs: {1:d} rt: {2:d} rd: {3:d} funct: {4:d} hex_code: {6:04x}\n{5:s}\n".format(
                        instruction,
                        rs,
                        rt,
                        rd,
                        funct,
                        pprintInstr([6, 11, 16, 21, 26], num),
                        num,
                    )
                )
            elif rtype_2:
                instr = rtype_2.group("instr")
                funct = functs[instr]
                opcode = opcodes[instr]
                rd, rs, rt = 0, 0, 0
                rs = int(rtype_2.group("rs")[1:])
                rt = int(rtype_2.group("rt")[1:])
                num = opcode << 26 | rs << 21 | rt << 16 | rd << 11 | funct
                debug(
                    "{0:s} rtype: rs: {1:d} rt: {2:d} rd: {3:d} funct: {4:d} hex_code: {6:04x}\n{5:s}\n".format(
                        instruction,
                        rs,
                        rt,
                        rd,
                        funct,
                        pprintInstr([6, 11, 16, 21, 26], num),
                        num,
                    )
                )
            elif rtype_3:
                instr = rtype_3.group("instr")
                funct = functs[instr]
                opcode = opcodes[instr]
                rd, rs, rt = 0, 0, 0
                rs = int(rtype_3.group("rs")[1:])
                rt = int(rtype_3.group("rt")[1:])
                rd = int(rtype_3.group("rd")[1:])
                num = opcode << 26 | rs << 21 | rt << 16 | rd << 11 | funct
                debug(
                    "{0:s} rtype: rs: {1:d} rt: {2:d} rd: {3:d} funct: {4:d} hex_code: {6:04x}\n{5:s}\n".format(
                        instruction,
                        rs,
                        rt,
                        rd,
                        funct,
                        pprintInstr([6, 11, 16, 21, 26], num),
                        num,
                    )
                )

            elif itype_2:
                instr = itype_2.group("instr")
                immediate = int(itype_2.group("immed"), 0)
                signed = instr in [
                    "addi",
                    "slti",
                    "lw",
                    "sw",
                    "beq",
                    "bne",
                    "blez",
                    "bgtz",
                ]
                unsigned = instr in ["sltiu", "andi", "ori", "xori"]
                imm_check(signed, False, immediate, lineNo)
                opcode = opcodes[instr]
                rs, rt = 0, 0
                rs = int(itype_2.group("rs")[1:])
                rt = int(itype_2.group("rt")[1:])
                num = opcode << 26 | rs << 21 | rt << 16 | (immediate & 65535)
                debug(
                    "{0:s} itype: rs: {1:d} rt: {2:d} hex_code: {4:04x}\n{3:s}\n".format(
                        instruction, rs, rt, pprintInstr([6, 11, 16], num), num
                    )
                )
            elif itype_1:
                instr = itype_1.group("instr")
                opcode = opcodes[instr]
                rs, rt = 0, 0
                rs = int(itype_1.group("rs")[1:])
                label = itype_1.group("label")
                # find label
                if label not in symbols:
                    raise AssemblerSyntaxError(lineNo, "unknown label %s" % label)
                instructionNo = symbols[label]
                offset = instructionNo - (instructionsSeen + 1)
                if offset > 2**15 - 1 or offset < -(2**15):
                    raise AssemblerRangeError(
                        lineNo,
                        "label %s is too far away: %d instructions from pc+1"
                        % (label, offset),
                    )
                num = opcode << 26 | rs << 21 | rt << 16 | (offset & 65535)
                debug(
                    "{0:s} itype: rs: {1:d} offset: {4:d} hex_code: {3:04x}\n{2:s}\n".format(
                        instruction, rs, pprintInstr([6, 11, 16], num), num, offset
                    )
                )

            elif branch:
                instr = branch.group("instr")
                opcode = opcodes[instr]
                rs = int(branch.group("rs")[1:])
                rt = int(branch.group("rt")[1:])
                label = branch.group("label")
                # find label
                if label not in symbols:
                    raise AssemblerSyntaxError(lineNo, "unknown label %s" % label)
                instructionNo = symbols[label]
                offset = instructionNo - (instructionsSeen + 1)
                if offset > 2**15 - 1 or offset < -(2**15):
                    raise AssemblerRangeError(
                        lineNo,
                        "label %s is too far away: %d instructions from pc+1"
                        % (label, offset),
                    )
                num = opcode << 26 | rs << 21 | rt << 16 | (offset & 65535)
                debug(
                    "{0:s} rs: {1:d} rt: {2:d} opcode: {3:d} offset: {4:d} hex_code: {5:04x}\n{6:s}\n".format(
                        instruction,
                        rs,
                        rt,
                        opcode,
                        offset,
                        num,
                        pprintInstr([6, 11, 16], num),
                    )
                )

            elif mem:
                instr = mem.group("instr")
                opcode = opcodes[instr]
                rs = int(mem.group("rs")[1:])
                rt = int(mem.group("rt")[1:])
                offset = int(mem.group("immed"), 0)
                imm_check(True, False, offset, lineNo)
                num = opcode << 26 | rs << 21 | rt << 16 | (offset & 65535)
                debug(
                    "{0:s} itype: rs: {1:d} rt: {2:d} hex_code: {4:04x}\n{3:s}\n".format(
                        instruction, rs, rt, pprintInstr([6, 11, 16], num), num
                    )
                )

            elif jtype:
                instr = jtype.group("instr")
                opcode = opcodes[instr]
                # find label
                label = jtype.group("label")
                if label not in symbols:
                    raise AssemblerSyntaxError(lineNo, "unknown label %s" % label)
                instructionNo = symbols[label]
                num = opcode << 26 | (instructionNo & 67108863)
                debug(
                    "{0:s} addr: {1:d} hex_code: {2:04x}\n{3:s}\n".format(
                        instruction, instructionNo, num, pprintInstr([6], num)
                    )
                )

            else:
                raise AssemblerSyntaxError(
                    lineNo, "Can't parse instruction '%s'" % instruction
                )
            # there's an instruction here, so increment the number of instructions
            instructionsSeen += 1
            instructions.append(num)
        lineNo += 1
    return instructions


def print_instructions(instructions, outputdir):

    hex_instructions = [("%04x" % inst).zfill(8) for inst in instructions]
    little_endian = [
        inst[6:8] + inst[4:6] + inst[2:4] + inst[0:2] for inst in hex_instructions
    ]

    used = little_endian
    bank0 = used[0::4]
    bank1 = used[1::4]
    bank2 = used[2::4]
    bank3 = used[3::4]

    for bank_name, bank in zip(
        ["Bank0", "Bank1", "Bank2", "Bank3"], [bank0, bank1, bank2, bank3]
    ):
        bf = open(os.path.join(outputdir, bank_name), "w")
        bf.write("v2.0 raw\n")
        bf.write(" ".join(bank))
        bf.close()
    with open(os.path.join(outputdir, "Bank"), "w") as file:
        file.write("v2.0 raw\n")
        file.write("\n".join(used))
        file.write("\nffffffff\n")


def debug(*args):
    if verbose:
        sys.stdout.write(" ".join([str(arg) for arg in args]) + "\n")


if __name__ == "__main__":
    usage = "%prog infile [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-o",
        "--out",
        dest="output_folder",
        type="string",
        default=".",
        help="Specify output folder to write the 4 memory bank dumps.",
    )
    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Verbose debug mode",
    )
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Incorrect command line arguments")
        sys.exit(1)

    verbose = options.verbose

    output_folder = options.output_folder
    input_file = args[0]
    # if re.match(r""".*(?P<extension>\.s)$""",input_file,re.I) and output_file == 'a.hex':
    # output_file = input_file[:-1] + "hex"

    try:
        infile = open(input_file)
    except IOError as e:
        print >> sys.stderr, "Unable to open input file %s" % input_file
        sys.exit(1)
    try:
        fill_symbol_table(infile)
        infile.seek(0)
        instructions = assemble_instructions(infile)
        infile.close()
    except AssemblerError as e:
        print >> sys.stderr, str(e)
        sys.exit(1)
    try:
        print_instructions(instructions, output_folder)
    except IOError as e:
        print >> sys.stderr, "Unable to write to output file %s" % output_file
        sys.exit(1)
    sys.exit(0)
