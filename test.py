import os
from itertools import tee
from decimal import Decimal
import sys
import re

in_dir = "./input_files"
out_dir = "./output_files"


def read_policy(text):
    policy = {}
    for line in text.split("\n"):
        if "->" in line:
            s = [x.strip().replace("\n", "") for x in line.split("->")]
            if len(s) == 2:
                policy[s[0]] = s[1]
    return policy


def compare_policies(p1, p2):
    print("Comparing Policies:")
    for a, b in zip(p1, p2):
        if p1[a] != p2[b]:
            print("The Policies are different")
            print(f"\t For node {a}, correct={p1[a]} test={p2[b]}")
            return False
    return True


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def read_values(text):
    values = {}
    for line in text.split("\n"):
        if "=" in line:
            x = [x.strip().replace("\n", "") for x in re.split(r"=| ", line)]
            i = 0
            for a, b in pairwise([x.strip().replace("\n", "") for x in re.split(r"=| ", line)]):
                if i % 2 != 0:
                    i += 1
                    continue
                values[a] = Decimal(b)
                i += 1
    return values


def compare_values(v1, v2, tolerance):
    print("Comparing Values:")
    for a, b in zip(v1, v2):
        if abs(v1[a] - v2[b]) > tolerance:
            print("The Values are different")
            print(f"\tFor node {a}, correct={v1[a]} text={v2[b]} diff={abs(v1[a] - v2[b])}")
            return False
    return True


if __name__ == '__main__':
    flags = {3: "-min", 6: "-df 0.9"}
    for i in range(1, 7):
        input_file = f"{in_dir}/input{i}.txt"
        output_file = f"{out_dir}/out{i}.txt"
        print(f"Testing file: {input_file}")
        with open(output_file, 'r') as file:
            test_out_n = file.read()
            if i in flags.keys():
                os.system(f"python3 mdp.py -tol 0.001 {flags[i]} {input_file} > output_test.txt")
            else:
                os.system(f"python3 mdp.py -tol 0.001 {input_file} > output_test.txt")
        with open(output_file) as f1:
            with open("output_test.txt") as f2:
                text_1 = f1.read()
                text_2 = f2.read()
                policy1 = read_policy(text_1)
                values1 = read_values(text_1)
                policy2 = read_policy(text_2)
                values2 = read_values(text_2)
                if not compare_values(values1, values2, 0.01) or not compare_policies(policy1, policy2):
                    print("Test Result: Fail")
                    sys.exit(1)
        print("Test Result: Pass")

