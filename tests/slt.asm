#slt

addi r1 r0 40
addi r2 r0 -40
slt r3 r2 r1
addi r1 r0 65
mult r3 r1
mflo r3
tty r3

#sltu

addi r1 r0 40
addi r2 r0 -40
sltu r3 r1 r2
addi r1 r0 65
mult r3 r1
mflo r3
tty r3

halt

#prints AA
