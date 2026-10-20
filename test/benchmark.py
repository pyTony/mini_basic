from mini_basic.display import PygameDisplay, TerminalDisplay
import timeit

def bench_terminal():
    d = TerminalDisplay(text_cols=80, text_rows=30)
    for _ in range(1000):
        d.set_text_dimensions(80, 30)

def bench_pygame():
    d = PygameDisplay(text_cols=80, text_rows=30, graphics_width=0)
    for _ in range(1000):
        d.set_text_dimensions(80, 30)

print("TerminalDisplay: ", timeit.timeit(bench_terminal, number=10))
print("PygameDisplay: ", timeit.timeit(bench_pygame, number=10))
