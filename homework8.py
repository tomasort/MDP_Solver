import numpy as np
import string
import pprint
from mdp import MDP

pp = pprint.PrettyPrinter(indent=4)

letters = [l for l in string.ascii_uppercase[:17]]
del letters[14]  # remove the O (because is too similar to 0)

grid = np.array(letters)
grid.resize((4, 4))

debug = False

print("Part 1 solution: ")
mdp1 = MDP(tolerance=0.001, max_iter=150)
mdp1.read_file("./input_files/homework8_parta.txt")
mdp1.solve()
mdp1.print_solution()
pp.pprint(mdp1)

print("\n\n")

print("Part 2 solution: ")
mdp2 = MDP(df=0.9, tolerance=0.001, max_iter=150)
mdp2.read_file("./input_files/homework8_partb.txt")
mdp2.solve()
mdp2.print_solution()
pp.pprint(mdp2)

