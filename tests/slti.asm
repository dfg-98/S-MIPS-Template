#slti

addi r2 r0 -40
slti r3 r2 40
addi r1 r0 65
mult r3 r1
mflo r3
tty r3

#sltiu

addi r2 r0 -1
sltiu r3 r2 40
addi r3 r0 65
mflo r3
tty r3

halt

#prints AA
