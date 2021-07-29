addi r1 r0 32
addi r2 r0 1
addi r3 r0 0
addi r4 r0 20
addi r5 r0 10
addi r8 r0 2

ciclo:
add r7 r2 r0
imprime:
divu r2 r5
mfhi r6
addi r6 r6 48
tty r6
mflo r2
bne r2 r0 imprime
tty r1
add r2 r7 r0
mulu r2 r8
mflo r2
addi r3 r3 1
bne r3 r4 ciclo

halt

# Deberia escribir todas las potencias de 2 del 0 al 19
# todas esritas con sus digitos en reversa
#prints 1 2 4 8 61 23 46 821 652 215 4201 8402 6904 2918 48361 86723 63556 270131 441262 882425
