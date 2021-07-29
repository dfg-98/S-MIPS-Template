addi r1 r0 4
addi r3 r0 20
mult r3 r1
mflo r4
tty r4
mfhi r5
addi r5 r5 100
tty r5

addi r1 r0 -4
addi r3 r0 20
mult r3 r1
mflo r4
addi r1 r0 -1
mult r4 r1
mflo r4
tty r4

halt

#prints PdP
