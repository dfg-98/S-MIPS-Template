addi r1 r0 165
addi r2 r0 165
bne r1 r2 end

addi r1 r0 7
bne r1 r2 print
halt
print:
addi r10 r0 65
tty r10
end:
halt

#prints A
