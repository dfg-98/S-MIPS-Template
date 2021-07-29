addi r1 r0 13
blez r1 end

addi r1 r0 -7
blez r1 print
halt
print:
addi r10 r0 65
tty r10
end:
halt

#prints A
