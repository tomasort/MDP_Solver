"""
Simple Flask MDP Solver Web UI
Single file application without blueprints
"""

import os
import sys
from flask import Flask, render_template, request, jsonify

# Add the parent directory to the path to import the MDP module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from mdp import MDP, Node, Policy

app = Flask(__name__)
app.config['DEBUG'] = True

# Global variables to store current MDP and solution
current_mdp = None
current_solution = None

def load_examples():
    """Load example MDP files"""
    examples = []
    examples_dir = os.path.join(parent_dir, 'tests', 'input_files')
    
    if os.path.exists(examples_dir):
        for filename in sorted(os.listdir(examples_dir)):
            if filename.endswith('.txt'):
                filepath = os.path.join(examples_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read().strip()
                    examples.append({
                        'name': filename.replace('.txt', '').replace('_', ' ').title(),
                        'filename': filename,
                        'content': content,
                        'description': f'Example MDP from {filename}'
                    })
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    return examples

def validate_mdp_input(input_text):
    """Validate MDP input and return statistics"""
    try:
        lines = input_text.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Create a temporary MDP to validate input
        temp_mdp = MDP()
        MDP.parse_input(temp_mdp, lines)
        
        return {
            'valid': True,
            'nodes': len(temp_mdp),
            'decision_nodes': len([n for n in temp_mdp.values() if n.is_decision()]),
            'chance_nodes': len([n for n in temp_mdp.values() if n.node_class == "chance"]),
            'terminal_nodes': len([n for n in temp_mdp.values() if n.is_terminal()]),
            'message': 'Input is valid'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'message': f'Error parsing input: {str(e)}'
        }

def solve_mdp_problem(input_text, df=1.0, tol=0.01, max_iter=100, use_min=False):
    """Solve the MDP and return results"""
    global current_mdp, current_solution
    
    try:
        print(f"Solving MDP with parameters: df={df}, tol={tol}, max_iter={max_iter}, use_min={use_min}")
        lines = input_text.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Create and solve MDP
        mdp = MDP(df=df, tol=tol, max_iter=max_iter, use_min=use_min)
        MDP.parse_input(mdp, lines)
        mdp.policy = Policy.random_policy(mdp)
        mdp.apply_policy(mdp.policy)
        mdp.solve()
        
        current_mdp = mdp
        
        # Prepare solution data
        policy_data = {}
        for key in sorted(mdp.policy.keys()):
            policy_data[key] = mdp.policy[key]
        
        node_values = {}
        nodes_data = {}
        edges_data = []
        
        for node_name in sorted(mdp.keys()):
            node = mdp[node_name]
            node_values[node_name] = float(round(node.value, 3))
            
            # Prepare node data
            nodes_data[node_name] = {
                'name': node_name,
                'value': float(round(node.value, 3)),
                'reward': float(node.reward),
                'type': node.node_class,
                'success_rate': float(node.success_rate) if node.success_rate else None
            }
            
            # Prepare edge data
            for target, prob in node.edges.items():
                edges_data.append({
                    'source': node_name,
                    'target': target,
                    'probability': float(prob),
                    'is_policy': node_name in policy_data and policy_data[node_name] == target
                })
        
        current_solution = {
            'policy': policy_data,
            'values': node_values,
            'nodes': nodes_data,
            'edges': edges_data,
            'success': True,
            'message': 'MDP solved successfully'
        }
        return current_solution
        
    except Exception as e:
        print(f"Error solving MDP: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': f'Error solving MDP: {str(e)}'
        }

@app.route('/')
def index():
    """Main page"""
    examples = load_examples()
    return render_template('index.html', examples=examples)

@app.route('/validate', methods=['POST'])
def validate():
    """Validate MDP input"""
    data = request.json
    input_text = data.get('input', '')
    result = validate_mdp_input(input_text)
    return jsonify(result)

@app.route('/solve', methods=['POST'])
def solve():
    """Solve MDP"""
    data = request.json
    input_text = data.get('input', '')
    
    # Get parameters with defaults
    df = float(data.get('discountFactor', 1.0))
    tol = float(data.get('tolerance', 0.01))
    max_iter = int(data.get('maxIterations', 100))
    use_min = data.get('minimize', False)
    
    result = solve_mdp_problem(input_text, df, tol, max_iter, use_min)
    return jsonify(result)

@app.route('/example/<filename>')
def get_example(filename):
    """Get a specific example by filename"""
    examples = load_examples()
    for example in examples:
        if example['filename'] == filename:
            return jsonify(example)
    return jsonify({'error': 'Example not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
