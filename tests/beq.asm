addi r1 r0 13
addi r2 r0 12
beq r1 r2 end

addi r1 r0 7
beq r1 r1 print
halt
print:
addi r10 r0 65
tty r10
end:
halt

#prints A