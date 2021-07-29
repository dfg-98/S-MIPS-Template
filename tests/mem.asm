addi r5 r0 65
addi r1 r0 24
sw r5 0(r1)
lw r8, 24(r0)
tty r8
halt

#prints A
