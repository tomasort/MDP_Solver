import os
import sys
from flask import Blueprint, request, jsonify

# Import services
from services.mdp_service import MDPSolverService
from services.example_service import ExampleService

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Create service instances
mdp_solver = MDPSolverService()
example_service = ExampleService()

@api_bp.route('/validate', methods=['POST'])
def validate_input():
    """Validate MDP input"""
    print("Validation endpoint called")
    data = request.json
    input_text = data.get('input', '')
    print(f"Validating input: {input_text[:100]}...")
    
    result = mdp_solver.validate_input(input_text)
    print(f"Validation result: {result}")
    return jsonify(result)

@api_bp.route('/solve', methods=['POST'])
def solve():
    """Solve MDP"""
    print("Solve endpoint called")
    data = request.json
    input_text = data.get('input', '')
    print(f"Solve input received: {input_text[:100]}...")
    
    # Get parameters with defaults
    df = float(data.get('discountFactor', 1.0))
    tol = float(data.get('tolerance', 0.01))
    max_iter = int(data.get('maxIterations', 100))
    use_min = data.get('minimize', False)
    
    result = mdp_solver.solve_mdp(input_text, df, tol, max_iter, use_min)
    print(f"Solve result success: {result.get('success', False)}")
    return jsonify(result)

@api_bp.route('/examples')
def get_examples():
    """Get example MDP inputs"""
    examples = example_service.load_examples()
    return jsonify(examples)

@api_bp.route('/examples/<filename>')
def get_example(filename):
    """Get a specific example by filename"""
    example = example_service.get_example_by_filename(filename)
    if example:
        return jsonify(example)
    else:
        return jsonify({'error': 'Example not found'}), 404
