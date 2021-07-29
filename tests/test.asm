addi r1, r0, 65
addi r2, r0, 66
sw r1, 44(r0)
sw r2, 940(r0)
lw r3, 940(r0)
lw r4, 44(r0)
tty r3
tty r4
sw r2 44(r0)
tty r2
halt

