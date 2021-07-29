addi r1 r0 0
addi r10 r0 10
cicle:
beq r1 r10 error

rnd r20
rnd r30
bne r20 r30 end
addi r1 r1 1
j cicle

end:
addi r1 r0 65
tty r1
halt

error:
halt

#prints A
