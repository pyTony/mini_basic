from mini_basic.display import PygameDisplay, TerminalDisplay
import timeit

def bench_terminal_newline():
    d = TerminalDisplay(text_cols=80, text_rows=30)
    for _ in range(10000):
        d._grid_newline()

def bench_pygame_newline():
    d = PygameDisplay(text_cols=80, text_rows=30, graphics_width=0)
    for _ in range(10000):
        d.newline()

print("Terminal newline: ", timeit.timeit(bench_terminal_newline, number=10))
print("Pygame newline: ", timeit.timeit(bench_pygame_newline, number=10))
