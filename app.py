from flask import Flask, request, jsonify, render_template
import json
import traceback
from mdp import MDP, Node, Policy
from decimal import Decimal

app = Flask(__name__)

def convert_json_to_mdp_text(states, transitions):
    """Convert JSON input to text format that mdp.py can parse"""
    lines = []
    
    # Add reward lines (state = reward)
    for state_name, state_data in states.items():
        reward = state_data.get('reward', 0)
        lines.append(f"{state_name} = {reward}")
    
    # Add edge lines (state : [edge1, edge2])
    for state_name, state_data in states.items():
        edges = state_data.get('edges', [])
        if edges:
            edges_str = ', '.join(edges)
            lines.append(f"{state_name} : [{edges_str}]")
    
    # Add probability lines (state % p1 p2 p3)
    for state_name, probs in transitions.items():
        if probs:
            probs_str = ' '.join([str(p) for p in probs])
            lines.append(f"{state_name} % {probs_str}")
    
    return lines

@app.route('/')
def index():
    """Serve the main UI page"""
    return render_template('index.html')

@app.route('/api/solve', methods=['POST'])
def solve_mdp():
    """Solve MDP from JSON input"""
    try:
        data = request.json
        
        # Extract parameters
        discount_factor = float(data.get('discount_factor', 0.9))
        tolerance = float(data.get('tolerance', 0.01))
        minimize = data.get('minimize', False)
        
        # Create MDP instance
        mdp = MDP(df=Decimal(str(discount_factor)), tol=Decimal(str(tolerance)), use_min=minimize)
        
        # Check if we have raw text input
        if 'text_input' in data and data['text_input'].strip():
            # Parse directly from text input
            text_lines = data['text_input'].strip().split('\n')
            MDP.parse_input(mdp, lines=text_lines)
        else:
            # Fallback to JSON parsing (for backwards compatibility)
            states = data.get('states', {})
            transitions = data.get('transitions', {})
            text_lines = convert_json_to_mdp_text(states, transitions)
            MDP.parse_input(mdp, lines=text_lines)
        
        # Initialize random policy and apply it
        mdp.policy = Policy.random_policy(mdp)
        mdp.apply_policy(mdp.policy)
         
        # Solve the MDP
        mdp.solve()
        
        # Prepare graph data for visualization
        nodes = []
        edges = []
        
        for state_name, node in mdp.items():
            # Create node data
            nodes.append({
                'id': state_name,
                'name': state_name,
                'value': float(node.value),
                'reward': float(node.reward),
                'type': 'state'
            })
            
            # Create edges for all possible transitions
            for edge_name, probability in node.edges.items():
                is_optimal = (mdp.policy.get(state_name) == edge_name)
                
                edges.append({
                    'source': state_name,
                    'target': edge_name,
                    'probability': float(probability),
                    'is_optimal': is_optimal
                })
        
        # Prepare response
        result = {
            'success': True,
            'policy': {name: str(action) for name, action in mdp.policy.items()},
            'values': {name: float(node.value) for name, node in mdp.items()},
            'converged': True,
            'graph': {
                'nodes': nodes,
                'edges': edges
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400

@app.route('/api/validate', methods=['POST'])
def validate_mdp():
    """Validate MDP structure"""
    try:
        data = request.json
        states = data.get('states', {})
        transitions = data.get('transitions', {})
        
        errors = []
        warnings = []
        
        # Basic validation
        if not states:
            errors.append("No states defined")
            
        for state_name, state_data in states.items():
            edges = state_data.get('edges', [])
            if state_name in transitions:
                probs = transitions[state_name]
                if len(edges) != len(probs):
                    errors.append(f"State {state_name}: number of edges doesn't match number of probabilities")
                if abs(sum(probs) - 1.0) > 0.001:
                    warnings.append(f"State {state_name}: probabilities don't sum to 1.0")
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [str(e)]
        }), 400

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example MDPs"""
    try:
        with open('examples/config.json', 'r') as config_file:
            config = json.load(config_file)
            examples = {}
            
            for example in config['examples']:
                example_id = example['id']
                examples[example_id] = {
                    'name': example['name'],
                    'description': example['description'],
                    'discount_factor': example['discount_factor'],
                    'tolerance': example['tolerance'],
                    'minimize': example.get('minimize', False)
                }
                
                # Add file path for frontend to request content
                examples[example_id]['file'] = example['file']
            
            return jsonify(examples)
    except Exception as e:
        return jsonify({
            'error': f"Failed to load examples: {str(e)}"
        }), 500

@app.route('/api/examples/<example_id>/content', methods=['GET'])
def get_example_content(example_id):
    """Get the content of a specific example file"""
    try:
        # Load config to get the file name
        with open('examples/config.json', 'r') as config_file:
            config = json.load(config_file)
            
        # Find the example with matching ID
        example_file = None
        for example in config['examples']:
            if example['id'] == example_id:
                example_file = example['file']
                break
        
        if not example_file:
            return jsonify({'error': 'Example not found'}), 404
            
        # Load the example file content
        file_path = f'examples/{example_file}'
        with open(file_path, 'r') as file:
            content = file.read()
            
        return jsonify({
            'success': True,
            'content': content,
            'id': example_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and parse MDP file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        content = file.read().decode('utf-8')
        
        # Parse the file using your existing parsing logic
        # This would need to be implemented based on your current file format
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'File uploaded successfully. Please implement parsing logic.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5051)
