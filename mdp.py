import re
import argparse
from decimal import Decimal
import sys
import random

comment = re.compile(r"^#.*$")
# reward lines are of the form 'name = value' where value is an integer
reward_line = re.compile(f"^[a-zA-Z0-9\-']+ *= *-?\.?[0-9]*$")
# edges are of the form 'name : [e1, e2, e2]' where each e# is the name of an out edge from name
edge_line = re.compile(f"^[a-zA-Z0-9\-']+ *: *\[ *([a-zA-Z0-9\-']*) *(, *[a-zA-Z0-9\-']*)* *\]$")
# probabilities are of the form 'name % p1 p2 p3'
probability_line = re.compile(f"^[a-zA-Z0-9\-']+ *% * (\.?[0-9]*| *)*$")
debug = False


def tokenize(line):
    """Separates the node name and the rest of the values depending on the type of the line"""
    if "=" in line:
        # tokenize the reward line
        tokens = [x.strip() for x in line.split("=")]
        return tokens[0], Decimal(tokens[1])
    if ":" in line:
        # tokenize the edge line
        tokens = [x.strip() for x in line.split(":")]
        edges = [x.strip() for x in tokens[1].strip("[]").split(',')]
        return tokens[0], edges
    if "%" in line:
        tokens = [x.strip() for x in line.split("%")]
        probabilities = [x.strip() for x in tokens[1].split(' ')]
        return tokens[0], probabilities


def print_d(*args, **kwargs):
    """Function to print stuff if we are in debug mode"""
    if debug:
        print(*args, **kwargs)


class Node:
    """This class represents a node in an MDP
        It can be a decision node, a terminal node or a chance node. """

    def __init__(self, name, reward=Decimal(0), node_class="chance", edges=None, success_rate=None, val=Decimal(0),
                 edge_order=None):
        if edge_order is None:
            edge_order = []
        if edges is None:
            edges = {}
        self.name = name
        self.reward = reward
        self.edges = edges
        self.node_class = node_class
        self.success_rate = success_rate
        self.value = val  # Every nodes starts with a value equal to its reward
        self.edge_order = edge_order  # list containing the edges from the input file. This is needed to maintain the order

    # a generator for computing the actions (the node that we want to move to and the probabilities for the edges) from the current state
    def actions(self):
        """Function that returns the set of actions available from the current node.
            This function is used in policy iteration to go through the various actions. """
        edge_probabilities = sorted(list(self.edges.values()), reverse=True)
        edge_names = list(self.edges.keys())
        for i in range(len(self.edges)):
            yield edge_names[i], {v1: v2 for v1, v2 in zip(edge_names, edge_probabilities)}
            # rotate edge_probabilities
            edge_probabilities = edge_probabilities[-1:] + edge_probabilities[:-1]

    def is_decision(self):
        return self.node_class == "decision"

    def is_terminal(self):
        return self.node_class == "terminal"

    def is_parent_of(self, possible_child):
        return possible_child.name in self.edges.keys()

    def add_edges(self, neighbors):
        self.edge_order = neighbors  # we need to keep the order of the edges. (this is specially important when there are duplicate edges)
        for e in neighbors:
            self.edges[e.strip()] = Decimal(0)  # The default probability is 0

    def add_probabilities(self, probabilities):
        if len(probabilities) == 1:
            success_rate = Decimal(probabilities[0])
            prob_for_other_edges = (1 - success_rate) / (len(self.edges) - 1)
            self.success_rate = success_rate
            self.node_class = "decision"
            # get the remaining probability and distribute it among the remaining edges
            for j, k_ in enumerate(self.edges.keys()):
                self.edges[k_] = success_rate if j == 0 else prob_for_other_edges
        else:
            p_sum = 0
            for j, e in enumerate(self.edge_order):
                p_sum += Decimal(probabilities[j])
                self.edges[e] += Decimal(probabilities[j])
            if p_sum != 1:
                sys.exit(1)

    def __repr__(self):
        # Mainly for debugging
        return f"{self.name}: class={self.node_class} edges={[(a, '%.3f' % float(round(b, 4))) for a, b in self.edges.items()]} " \
               f"success_rate={self.success_rate} value={'%.2f' % round(self.value, 5)} reward={'%.2f' % self.reward}"

    def __hash__(self):
        return self.name.__hash__()

    def copy(self):
        return Node(self.name, self.reward, self.node_class, self.edges, self.success_rate, self.value)


class Policy(dict):
    """A class to specify the policy of an MDP. A Policy is simply a mapping between Decision nodes and Actions"""

    def __init__(self, iterable=None):
        """If random_policy is true then we initialize a random policy for the given graph. If it is false we initialize an empty policy"""
        if iterable is None:
            iterable = {}
        super(Policy, self).__init__(iterable)

    @staticmethod
    def random_policy(graph):
        """This function initializes the policy as a random policy for the given graph"""
        policy = Policy()
        for k in graph.keys():
            if graph[k].is_decision():
                policy[k] = random.choice(list(graph[k].edges.keys()))
        return policy

    def __str__(self):
        policy = []
        for key in sorted(list(self.keys())):
            policy.append(f"{key} -> {self[key]}\n")
        return "".join(policy)

    def copy(self):
        return Policy(self)

    def __eq__(self, other):
        if (not self or not other) and not (len(self) == 0 and len(other) == 0):
            return False
        for a, b in zip(self, other):
            if self[a] != other[b]:
                return False
        return True


class MDP(dict):
    """A class for an MDP.
        It contains methods for manipulating, solving and printing MDPs and MRPs"""

    def __init__(self, df=1.0, policy=None, tol=0.01, max_iter=100, use_min=False):
        """df: discount factor"""
        super(MDP, self).__init__()
        if policy is None:
            policy = Policy()
        self.policy = policy
        self.df = df
        self.tol = tol
        self.max_iter = max_iter
        self.use_min = use_min

    def copy(self):
        new_mdp = MDP(self.df, self.policy, self.tol, self.max_iter, self.use_min)
        for k, v in self.items():
            new_mdp[k] = v
        return new_mdp

    def solve(self):
        """Solves the MDP using value iteration and greedy policy iteration"""
        current_policy = self.policy.copy()
        while True:
            self.value_iteration()
            self.policy_iteration()
            previous_policy = current_policy.copy()
            current_policy = self.policy.copy()
            self.apply_policy(self.policy)
            if previous_policy == current_policy:
                break
        self.apply_policy(self.policy)

    def apply_policy(self, policy):
        for node in self.values():
            if node.is_decision():
                for e in node.edges.keys():
                    if e == policy[node.name]:
                        node.edges[e] = node.success_rate
                    else:
                        node.edges[e] = (1 - node.success_rate) / (len(node.edges) - 1)

    def policy_iteration(self):
        print_d(f"Going into Policy Iteration:")
        if not self.policy:
            self.policy = Policy.random_policy(self)
        current_policy = self.policy.copy()
        iter_num = 0
        while True:
            new_policy = current_policy.copy()
            for node in self.values():
                best_action = None
                best_action_value = float("-inf")
                if self.use_min:
                    best_action_value = float("+inf")
                if node.is_decision():
                    print_d(f"Looking for best action in {node.name}")
                    for action, probabilities in node.actions():
                        new_policy[node.name] = action
                        print_d(f"\tTesting Policy: {node.name} -> {action}")
                        action_value = self.value(node, new_policy)
                        print_d(f"\t\t\tAction {node.name} -> {action} has a value of {action_value}")
                        if (best_action_value < action_value and not self.use_min) or (
                                best_action_value > action_value and self.use_min):
                            print_d(f"\tBest Action at {node.name}: {node.name} -> {action}")
                            best_action_value = action_value
                            best_action = action
                    if best_action:
                        new_policy[node.name] = best_action
            previous_policy = current_policy.copy()
            current_policy = new_policy.copy()
            if previous_policy == current_policy:
                print_d(f"The Policies ARE equal. Iterations: {iter_num}")
                print_d(f"Previous Policy: {previous_policy}")
                print_d(f"Current Policy: {current_policy}")
                break
            print_d(f"The Policies are NOT equal. Iterations: {iter_num}")
            print_d(f"Previous Policy: {previous_policy}")
            print_d(f"Current Policy: {current_policy}")
            iter_num += 1
        self.policy = new_policy.copy()

    def value_iteration(self):
        print_d(f"Going into Value Iteration:")
        print_d(f"Using policy: {self.policy}")
        current_values = {k: v.value for k, v in self.items()}
        iter_num = 0
        if not self.policy:
            self.policy = Policy.random_policy(self)
        while True:
            new_values = {}
            for node in self.values():
                new_values[node] = self.value(node, self.policy)
            previous_values = current_values.copy()
            for node in new_values.keys():
                self[node.name].value = new_values[node]
            current_values = new_values.copy()

            # Test to see if the current values and the previous values are sufficiently similar
            values_converge = True
            if not previous_values or not current_values:
                values_converge = False
            for a, b in zip(previous_values, current_values):
                if abs(previous_values[a] - current_values[b]) > self.tol:
                    values_converge = False
            if values_converge or iter_num >= self.max_iter:
                print_d(f"The values ARE equal. Iteration: {iter_num}")
                print_d(f"Previous values: {previous_values}")
                print_d(f"Current values: {current_values}")
                break
            print_d(f"The values are NOT equal. Iteration: {iter_num}")
            print_d(f"Previous values: {previous_values}")
            print_d(f"Current values: {current_values}")
            iter_num += 1

    def value(self, state, policy=None):
        if not policy:
            policy = self.policy
        probabilities = state.edges
        expected_utility = 0
        if state.is_decision():
            action = policy[state.name]
            edges = list(state.edges.keys())
            probabilities = {e: state.success_rate if e == action else Decimal((1 - state.success_rate) / (len(edges) - 1)) for e in edges}
        for node_name, prob in probabilities.items():
            expected_utility += Decimal(self.df) * Decimal(prob) * self[node_name].value
        return Decimal(state.reward) + expected_utility

    def print_solution(self):
        """Prints solution in the format required for the assignment. It also displays the values in alphabetical order"""
        print(self.policy.__str__())
        values = []
        for node_name in sorted(list(self.keys())):
            values.append(f"{node_name}={'%.3f' % round(self[node_name].value, 3)}")
        print(" ".join(values))

    @staticmethod
    def read_file(file_name, df=1.0, tol=0.01, max_iter=100, use_min=False):
        mdp_from_file = MDP(df, None, tol, max_iter, use_min)
        lines = []
        with open(file_name) as in_file:
            for line in in_file.readlines():
                lines.append(line)
        MDP.parse_input(mdp_from_file, lines=lines)
        mdp_from_file.policy = Policy.random_policy(mdp_from_file)
        mdp_from_file.apply_policy(mdp_from_file.policy)
        return mdp_from_file

    @staticmethod
    def parse_input(output_mdp, lines=[]):
        unclaimed_probability_lines = []
        while True:
            for i, line in enumerate(lines):
                line = line.replace("\n", '')
                if comment.match(line) or line == '':
                    print_d(f"line #{i}: {line} {'EMPTY LINE' if len(line) == 0 else 'COMMENT'}")
                    continue
                # Figure out what kind of line this line is.
                elif reward_line.match(line):
                    print_d(f"line #{i}: {line} REWARD/COST")
                    node_name, reward_value = tokenize(line)
                    # if the node is already in the graph, add the reward to the node if not, create a new node
                    if node_name in output_mdp.keys():
                        output_mdp[node_name].reward = Decimal(reward_value)
                    else:
                        output_mdp[node_name] = Node(node_name, Decimal(reward_value))
                elif edge_line.match(line):
                    print_d(f"line #{i}: {line} EDGE")  # name: [e1, e2, e2]
                    node_name, neighbors = tokenize(line)
                    if node_name not in output_mdp.keys():
                        output_mdp[node_name] = Node(node_name)
                    output_mdp[node_name].add_edges(neighbors)
                elif probability_line.match(line):
                    print_d(f"line #{i}: {line} PROBABILITIES")
                    node_name, probabilities = tokenize(line)
                    if node_name not in output_mdp.keys():
                        unclaimed_probability_lines.append(line)
                        continue
                    # Check if we have a decision node.
                    output_mdp[node_name].add_probabilities(probabilities)
                else:
                    print_d("NO MATCH")
            if unclaimed_probability_lines:
                # claim the unclaimed probabilities with one more pass.
                lines = unclaimed_probability_lines
            else:
                break
        for k, v in output_mdp.items():
            # Look for nodes with no edges. These nodes are terminal nodes.
            if not output_mdp[k].edges:
                output_mdp[k].node_class = "terminal"

        for k, v in output_mdp.items():
            # Look for nodes with edges but no probabilities it is assumed to be a decision node with success_rate=1
            if all(x == 0 for x in v.edges.values()) and not v.is_terminal():
                if v.node_class != "decision":  # we don't want to mess with the nodes that are already decision nodes but
                    if len(v.edges) != 1:
                        v.node_class = "decision"
                        v.success_rate = 1
                    for i, key in enumerate(v.edges.keys()):
                        v.edges[
                            key] = 1 if i == 0 else 0  # we set the policy to the first edge we encounter (we might still use a random policy for policy iteration)

    # def print_as_tree(self, layout='breadthfirst', root=None, node_dist=1):
    #     tree_mdp = self.copy()
    #     if root is None:
    #         root = list(tree_mdp.keys())[0]
    #     size_y = 700
    #     nodes = [{'data': {'id': x.name, 'label': f"{x.name.upper()}", 'node_label': f"{x.name.upper()}, val: {round(x.value, 3)}", }, 'classes': x.node_class,
    #               'position': {'x': random.randint(0, size_y), 'y': random.randint(0, size_y)}} for x in tree_mdp.values()]
    #     edges = []
    #     current_nodes = list(tree_mdp.keys())
    #     for i in current_nodes:
    #         for node_name in tree_mdp.keys():
    #             if tree_mdp[node_name].is_parent_of(tree_mdp[i]):
    #                 # change the parent node and add a new node
    #                 pass
    #                 # tree_mdp[node_name].edges[]
    #     for i in tree_mdp.keys():
    #         # Find all the parents of i
    #         for k, val in tree_mdp[i].edges.items():
    #             edge_specification = {
    #                 'data': {'id': f"{i}{k}",
    #                          'source': i,
    #                          'target': k,
    #                          'weight': round(val, 3)
    #                          }
    #             }
    #             if i in tree_mdp.policy.keys() and tree_mdp.policy[i] == k:
    #                 edge_specification['style'] = {'line-color': 'red'}
    #             edges.append(edge_specification)
    #     return cyto.Cytoscape(
    #         id="MDP graph",
    #         layout={'name': layout, 'roots': f"#{root}", 'spacingFactor': node_dist},
    #         style={'wdith': '100%', 'height': f"{size_y}px"},
    #         elements=nodes + edges,
    #         stylesheet=
    #         [
    #             {
    #                 'selector': 'node',
    #                 'style': {
    #                     'content': 'data(node_label)',
    #                 }
    #             },
    #             {
    #                 'selector': 'edge',
    #                 'style': {
    #                     'curve-style': 'bezier',
    #                     'target-arrow-shape': 'triangle',
    #                     'label': 'data(weight)'
    #                 }
    #             },
    #             {
    #                 'selector': '.terminal',
    #                 'style': {
    #                     'shape': 'triangle'
    #                 }
    #             },
    #             {
    #                 'selector': '.decision',
    #                 'style': {
    #                     'shape': 'square'
    #                 }
    #             }
    #         ]


if __name__ == '__main__':
    # Parse the command line arguments
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
    parser.add_argument('-t', required=False, action='store_true',
                        help='flag for running a flask app that displays a graph for the MDP')
    parser.add_argument('filename', help='Input file')
    args = parser.parse_args(sys.argv[1:])
    debug = args.d

    # Create the MDP and solve it.
    mdp = MDP.read_file(args.filename, df=args.df, tol=args.tol, max_iter=args.iter, use_min=args.min)
    mdp.solve()
    mdp.print_solution()
    # if args.t:
    #     import dash
    #     import dash_cytoscape as cyto
    #     from dash import html
    #
    #     app = dash.Dash(__name__)
    #     app.layout = html.Div([mdp.print_as_tree(root='Office', layout='circle', node_dist=0.7)])
    #     app.run_server(debug=True)

