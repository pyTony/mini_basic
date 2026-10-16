    10 PRINT "=== HEAVY-DUTY BASIC BENCHMARK === "
    20 PRINT "Testing deep recursion limits..."
    25 PRINT "Ackermann growth is explosive: keep M<=3 and raise N to control the load (M=4,N=2+ will not finish in practical time)."
    30 INPUT "Enter M (recommend 1-3): ", M
    40 INPUT "Enter N (recommend 1-14; N=12 takes about a second, N=14 several seconds): ", N
    50 T1 = TIMER ' Start the benchmark clock
    60 PRINT "Result: "; FNACK(M, N)
    70 T2 = TIMER ' End the benchmark clock
    80 PRINT "Total Execution Time: "; T2 - T1;" seconds"
    90 END
   100 FUNCTION FNACK(M, N)
   110   IF M = 0 THEN FNACK = N + 1: EXIT FUNCTION
   120   IF N = 0 THEN FNACK = FNACK(M - 1, 1): EXIT FUNCTION
   130   FNACK = FNACK(M - 1, FNACK(M, N - 1))
   140 END FUNCTION
