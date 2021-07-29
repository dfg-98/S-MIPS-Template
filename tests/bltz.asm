addi r1 r0 100
bltz r1 end

addi r1 r0 -2586
bltz r1 print
halt
print:
addi r10 r0 65
tty r10
end:
halt

#prints A
