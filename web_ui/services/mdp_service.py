"""MDP solving service module"""

import os
import sys

# Add the parent directory to the path to import the MDP module
current_dir = os.path.dirname(os.path.abspath(__file__))
web_ui_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_ui_dir)
sys.path.append(parent_dir)

from mdp import MDP, Node, Policy

class MDPSolverService:
    """Service class for MDP solving operations"""
    
    def __init__(self):
        self.current_mdp = None
        self.solution = None
    
    def validate_input(self, input_text):
        """Parse MDP input text and return validation results"""
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
            print(f"Validation error: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'message': f'Error parsing input: {str(e)}'
            }
    
    def solve_mdp(self, input_text, df=1.0, tol=0.01, max_iter=100, use_min=False):
        """Solve the MDP and return results"""
        try:
            print(f"Starting MDP solving with parameters: df={df}, tol={tol}, max_iter={max_iter}, use_min={use_min}")
            lines = input_text.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            print(f"Input lines: {lines}")
            
            # Create and solve MDP
            mdp = MDP(df=df, tol=tol, max_iter=max_iter, use_min=use_min)
            MDP.parse_input(mdp, lines)
            mdp.policy = Policy.random_policy(mdp)
            mdp.apply_policy(mdp.policy)
            print("Starting solve...")
            mdp.solve()
            print("Solve completed successfully")
            
            self.current_mdp = mdp
            
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
                
                # Prepare node data for visualization
                nodes_data[node_name] = {
                    'name': node_name,
                    'value': float(round(node.value, 3)),
                    'reward': float(node.reward),
                    'type': node.node_class,
                    'success_rate': float(node.success_rate) if node.success_rate else None
                }
                
                # Prepare edge data for visualization
                for target, prob in node.edges.items():
                    edges_data.append({
                        'source': node_name,
                        'target': target,
                        'probability': float(prob),
                        'is_policy': node_name in policy_data and policy_data[node_name] == target
                    })
            
            self.solution = {
                'policy': policy_data,
                'values': node_values,
                'nodes': nodes_data,
                'edges': edges_data,
                'success': True,
                'message': 'MDP solved successfully'
            }
            return self.solution
        except Exception as e:
            print(f"Error during MDP solving: {str(e)}")
            # Ensure to log the full traceback for debugging
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error solving MDP: {str(e)}'
            }

    def get_current_solution(self):
        """Get the current solution"""
        return self.solution
