import re
import argparse
from decimal import Decimal
import sys
import pprint
import random

import dash
import dash_cytoscape as cyto
from dash import html

# Our initial policy is to apply the success rate to the first edge in the list of edges (we are using a dictionary)

alphanumeric = re.compile(r"[a-zA-Z0-9]+")
comment = re.compile(r"^#.*$")
value = re.compile(r"[0-9\-]*")
# rc lines are of the form 'name = value' where value is an integer
rc_line = re.compile(f"^[a-zA-Z0-9\-]+ *= *-?[0-9]*$")
# edges are of the form 'name : [e1, e2, e2]' where each e# is the name of an out edge from name
edge_line = re.compile(f"^[a-zA-Z0-9]+ *: *\[ *([a-zA-Z0-9]*) *(, *[a-zA-Z0-9]*)* *\]$")
# probabilities are of the form 'name % p1 p2 p3'
probability_line = re.compile(f"^[a-zA-Z0-9]+ *% * (\.*[0-9]*| *)*$")
pp = pprint.PrettyPrinter(indent=4)
debug = False


def print_d(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


class Policy(dict):
    """A class to specify the policy of an MDP. A Policy is simply a mapping between Decision nodes and Actions"""

    def __init__(self, iterable=None):
        """If random_policy is true then we initialize a random policy for the given graph. If it is false we initialize an empty policy"""
        if iterable:
            super(Policy, self).__init__(iterable)
        else:
            super(Policy, self).__init__()

    def random_policy(self, graph):
        """This function initializes the policy as a random policy for the given graph"""
        for k in graph.keys():
            if graph[k].is_decision:
                self[k] = random.choice(list(graph[k].edges.keys()))

    def __str__(self):
        policy = []
        for key in sorted(list(self.keys())):
            policy.append(f"{key} -> {self[key]}\n")
        return "".join(policy)

    def __copy__(self):
        return self.__init__(self)


class MDP(dict):
    """A class for an MDP graph"""

    def __init__(self, df=1.0, policy=None, tolerance=0.01, max_iter=100, use_min=False):
        """df: discount factor"""
        super(MDP, self).__init__()
        self.policy = policy
        self.df = df
        self.tolerance = tolerance
        self.max_iter = max_iter
        self.use_min = use_min

    def solve(self):
        current_policy = self.policy
        while True:
            self.value_iteration()
            self.policy_iteration()
            previous_policy = current_policy
            current_policy = self.policy.copy()
            self.apply_policy(self.policy)
            if self.policies_converge(previous_policy, current_policy):
                break
        self.apply_policy(self.policy)

    def apply_policy(self, policy):
        for node in self.values():
            if node.is_decision:
                for e in node.edges.keys():
                    if e == policy[node.name]:
                        node.edges[e] = node.success_rate
                    else:
                        node.edges[e] = (1 - node.success_rate) / (len(node.edges) - 1)

    def policy_iteration(self):
        if not self.policy:
            self.policy.random_policy(self)
        current_policy = self.policy
        iter_num = 0
        while True:
            new_policy = current_policy
            for node in self.values():
                best_action = None
                best_action_value = float("-inf")
                if self.use_min:
                    best_action_value = float("+inf")
                if node.is_decision:
                    for action, probabilities in node.actions():
                        new_policy[node.name] = action
                        print_d(f"Testing Policy: {node.name} -> {action}")
                        action_value = self.value(node, new_policy)
                        print_d(f"Action {node.name} -> {action} has a value of {action_value}")
                        if (best_action_value < action_value and not self.use_min) or (
                                best_action_value > action_value and self.use_min):
                            print_d(f"Action {node.name} -> {action} Is the current best action")
                            best_action_value = action_value
                            best_action = action
                    if best_action:
                        new_policy[node.name] = best_action
            previous_policy = current_policy
            current_policy = new_policy
            if self.policies_converge(previous_policy, current_policy):
                break
            iter_num += 1
        self.policy = new_policy

    def value_iteration(self, policy=None):
        current_values = {k: v.value for k, v in self.items()}
        iter_num = 0
        if not policy:
            if not self.policy:
                self.policy = Policy()
                self.policy.random_policy(self)
            policy = self.policy
        while True:
            new_values = {}
            for node in self.values():
                # for action, probabilities in node.actions():
                new_values[node] = self.value(node, policy)
            previous_values = current_values
            for node in new_values.keys():
                self[node.name].value = new_values[node]
            current_values = new_values
            if self.values_converge(previous_values, current_values) or iter_num >= self.max_iter:
                break
            iter_num += 1

    def values_converge(self, previous_values, current_values):
        if not previous_values or not current_values:
            return False
        for a, b in zip(previous_values, current_values):
            if abs(previous_values[a] - current_values[b]) > self.tolerance:
                return False
        return True

    @staticmethod
    def policies_converge(previous_policy, current_policy):
        if (not previous_policy or not current_policy) and (previous_policy != current_policy):
            return False
        for a, b in zip(previous_policy, current_policy):
            if previous_policy[a] != current_policy[b]:
                return False
        return True

    def value(self, state, policy=None):
        if not policy:
            policy = self.policy
        probabilities = state.edges
        expected_utility = 0
        if state.is_decision:
            action = policy[state.name]
            edges = list(state.edges.keys())
            probabilities = {}
            for e in edges:
                if e == action:
                    probabilities[e] = state.success_rate
                else:
                    probabilities[e] = Decimal((1 - state.success_rate) / (len(edges) - 1))
        # print(f"Calculating The expected utility for state {state.name} with edges {list(state.edges.keys())}")
        for node_name, prob in probabilities.items():
            # print(f"\t{node_name} E += {self.df} * {prob} * {self[node_name].value} = {Decimal(self.df) * Decimal(prob) * self[node_name].value} ")
            expected_utility += Decimal(self.df) * Decimal(prob) * self[node_name].value
        # state.value = state.rc + expected_utility
        # print(f"\t Utility = {state.rc} + {expected_utility} = {state.rc + expected_utility}")
        return Decimal(state.rc) + expected_utility

    def print_policy(self):
        print(self.policy)

    def print_values(self):
        values = []
        for node_name in sorted(list(self.keys())):
            values.append(f"{node_name}={'%.3f' % round(self[node_name].value, 3)}")
        print(" ".join(values))

    def print_solution(self):
        self.print_policy()
        self.print_values()

    def print_as_tree(self):
        size = 400
        nodes = [{'data': {'id': x.name, 'label': f"{x.name.upper()}, {x.value}"},
                  'position': {'x': random.randint(0, size), 'y': random.randint(0, size)}} for x in self.values()]
        edges = []
        for i in self.keys():
            for k, val in self[i].edges.items():
                edges.append({'data': {'id': f"{i}{k}", 'source': i, 'target': k, 'weight': val}})
        return cyto.Cytoscape(
            id="MDP graph",
            layout={'name': 'preset'},
            style={'wdith': '100%', 'height': f"{size}px"},
            elements=nodes + edges,
            stylesheet=
            [
                {
                    'selector': 'node',
                    'style': {
                        'content': 'data(label)',
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'curve-style': 'bezier',
                        'source-arrow-shape': 'triangle',
                        'label': 'data(weight)'
                    }
                }]
        )

    def read_file(self, file_name):
        lines = []
        with open(file_name) as in_file:
            for line in in_file.readlines():
                lines.append(line)
        self.parse_input(lines=lines)

    def parse_input(self, lines=None):
        if lines is None:
            lines = []
        unclaimed_probabilities = []
        for i, line in enumerate(lines):
            line_ = line.replace('\n', '')
            print_d(f"line #{i}: {line_}", end=' ')
            if line == '\n' or comment.match(line_):
                print_d()
                continue
            # Figure out what kind of line line is.
            elif rc_line.match(line_):
                print_d("REWARD/COST")
                symbols = [x.strip() for x in line_.split("=")]
                if symbols[0] in self.keys():
                    # if the node is already in the graph, add the reward/cost value
                    self[symbols[0]].rc = Decimal(symbols[1])
                    # self[symbols[0]].value = Decimal(symbols[1])
                else:
                    # if the node not in the graph, create a new node
                    self[symbols[0]] = Node(symbols[0], Decimal(symbols[1]))
            elif edge_line.match(line_):
                print_d("EDGE")
                # name: [e1, e2, e2]
                symbols = [x.strip() for x in line_.split(":")]
                node_name = symbols[0]
                edges = [x.strip() for x in symbols[1].strip("[]").split(',')]
                if node_name not in self.keys():
                    self[node_name] = Node(node_name)
                self[node_name].edge_line = edges
                for e in edges:
                    new_edge = e.strip()
                    # add e to the edges of the node with name node_name
                    # For arbitrary (and honestly silly) reasons we don't have the probability right now so we just use None as a placeholder
                    self[node_name].edges[e] = None
            elif probability_line.match(line_):
                print_d("PROBABILITIES")
                # name % p1 p2 p3
                symbols = [x.strip() for x in line_.split("%")]
                node_name = symbols[0]
                edge_probabilities = [x.strip() for x in symbols[1].split(' ')]
                if node_name not in self.keys():
                    unclaimed_probabilities.append(line_)
                else:
                    if len(edge_probabilities) == 1:
                        # decision node
                        success_rate = Decimal(edge_probabilities[0])
                        prob_for_other_edges = (1 - success_rate) / (len(self[node_name].edges) - 1)
                        self[node_name].success_rate = success_rate
                        self[node_name].is_decision = True
                        # get the remaining probability and distribute it among the remaining edges
                        for j, k_ in enumerate(self[node_name].edges.keys()):
                            if j == 0:
                                self[node_name].edges[k_] = success_rate
                            else:
                                self[node_name].edges[k_] = prob_for_other_edges
                    else:
                        # chance node
                        p_sum = 0
                        # TODO: Fix this patch. There is a problem with repeated edges
                        if not self[node_name].edge_line:
                            for j, e in enumerate(self[node_name].edges.keys()):
                                p_sum += Decimal(edge_probabilities[j])
                                if self[node_name].edges[e] is None:
                                    self[node_name].edges[e] = Decimal(edge_probabilities[j])
                                else:
                                    self[node_name].edges[e] += Decimal(edge_probabilities[j])
                            if p_sum != 1:
                                print("The probabilities must add up to 1")
                                sys.exit(1)
                        else:
                            for j, e in enumerate(self[node_name].edge_line):
                                p_sum += Decimal(edge_probabilities[j])
                                if self[node_name].edges[e] is None:
                                    self[node_name].edges[e] = Decimal(edge_probabilities[j])
                                else:
                                    self[node_name].edges[e] += Decimal(edge_probabilities[j])
                        if p_sum != 1:
                            print("The probabilities must add up to 1")
                            sys.exit(1)
            else:
                print_d("NO MATCH")
        # claim the unclaimed probabilities
        if unclaimed_probabilities:
            self.parse_input(lines=unclaimed_probabilities)
        # Look for nodes with no edges.
        #   These nodes are terminal nodes. A probability entry for such a node is an error
        for k, v in self.items():
            if not self[k].edges:
                self[k].is_terminal = True

        # Look for nodes with edges but no probabilities
        #   If a node has edges but no probability entry, it is assumed to be a decision node with p=1
        for k, v in self.items():
            if all(x is None for x in v.edges.values()) and not v.is_terminal:
                if len(v.edges) != 1:
                    v.is_decision = True
                    v.success_rate = 1
                for i, k_ in enumerate(v.edges.keys()):
                    if i == 0:
                        v.edges[k_] = 1
                    else:
                        v.edges[k_] = 0


class Node:
    """This class represents a node in an MDP"""

    def __init__(self, name, rc=0, decision_node=False):
        self.name = name
        self.rc = rc
        self.edges = {}
        self.is_decision = decision_node
        self.success_rate = None
        self.is_terminal = False
        self.value = rc  # Every nodes starts with a value equal to its reward
        self.edge_line = None  # String containing the edge line from the input file

    # a generator for computing the actions (the node that we want to move to and the probabilities for the edges) from the current state
    def actions(self):
        """Function that returns the set of actions available from the current  node"""
        edge_probabilities = sorted(list(self.edges.values()), reverse=True)
        edge_names = list(self.edges.keys())
        for i in range(len(self.edges)):
            yield edge_names[i], {v1: v2 for v1, v2 in zip(edge_names, edge_probabilities)}
            # rotate edge_probabilities
            edge_probabilities = edge_probabilities[-1:] + edge_probabilities[:-1]

    def __repr__(self):
        return f"{self.name}: edges={[(a, '%.3f' % float(round(b, 4))) for a, b in self.edges.items()]} decision={self.is_decision} " \
               f"success_rate={self.success_rate} terminal={self.is_terminal} value={'%.2f' % round(self.value, 5)} reward={'%.2f' % self.rc}"

    def __hash__(self):
        return self.name.__hash__()


app = dash.Dash(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Markov Process Solver: A generic markov process solver')
    parser.add_argument('-df', nargs='?', type=float, required=False, default=1.0,
                        help="Discount factor [0, 1] to use on future rewards, defaults to 1.0")
    parser.add_argument('-min', required=False, action='store_true',
                        help='minimize values as costs, defaults to false which maximizes values as rewards')
    parser.add_argument('-tol', nargs='?', default=0.01, type=float, required=False,
                        help='Tolerance for exiting value iteration, defaults to 0.01')
    parser.add_argument('-iter', nargs='?', default=100, type=float, required=False,
                        help='Integer that indicates a cutoff for value iteration, defaults to 100')
    parser.add_argument('-d', required=False, action='store_true',
                        help='flag for debugging. It prints the attributes of the nodes before and after solving the MDP')
    parser.add_argument('filename', help='Input file')
    args = parser.parse_args(sys.argv[1:])
    debug = args.d
    mdp = MDP(df=args.df, tolerance=args.tol, max_iter=args.iter, use_min=args.min)
    mdp.read_file(args.filename)
    mdp.solve()
    mdp.print_solution()
    app.layout = html.Div([mdp.print_as_tree()])
    app.run_server(debug=True)
