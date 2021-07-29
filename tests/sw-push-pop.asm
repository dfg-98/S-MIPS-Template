addi r1 r0 65
sw r1 0(r1)
addi r1 r1 -5
push r1
pop r31
pop r1
tty r1
halt

#prints A
