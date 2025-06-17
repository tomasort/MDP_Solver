"""
Dash-based MDP Solver Web UI
Enhanced with interactive Plotly graphs
"""

import os
import sys
import json
from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Add the parent directory to the path to import the MDP module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from mdp import MDP, Node, Policy

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "MDP Solver"

# Global variables
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
                        'label': filename.replace('.txt', '').replace('_', ' ').title(),
                        'value': content
                    })
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    return examples

def validate_mdp_input(input_text):
    """Validate MDP input and return statistics"""
    try:
        lines = input_text.strip().split('\n')
        # Filter out comments and empty lines
        lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        terminal_nodes = 0
        decision_nodes = 0
        chance_nodes = 0
        
        for line in lines:
            if '=' in line and ':' not in line:
                terminal_nodes += 1
            elif ':' in line and '%' not in line:
                decision_nodes += 1
            elif '%' in line:
                chance_nodes += 1
        
        total_nodes = terminal_nodes + decision_nodes + chance_nodes
        
        return {
            'valid': total_nodes > 0,
            'nodes': total_nodes,
            'terminal_nodes': terminal_nodes,
            'decision_nodes': decision_nodes,
            'chance_nodes': chance_nodes,
            'message': 'Valid MDP definition' if total_nodes > 0 else 'No valid nodes found'
        }
    except Exception as e:
        return {
            'valid': False,
            'nodes': 0,
            'terminal_nodes': 0,
            'decision_nodes': 0,
            'chance_nodes': 0,
            'message': str(e)
        }

def solve_mdp(input_text, discount_factor=1.0, tolerance=0.01, max_iterations=100, minimize=False):
    """Solve the MDP and return results"""
    global current_mdp, current_solution
    
    try:
        # Parse and solve MDP
        current_mdp = MDP(input_text)
        current_mdp.solve(discount_factor=discount_factor, tolerance=tolerance, max_iterations=max_iterations, minimize=minimize)
        
        # Prepare solution data
        policy_data = {}
        for key in sorted(current_mdp.policy.keys()):
            policy_data[key] = current_mdp.policy[key]
        
        node_values = {}
        nodes_data = {}
        edges_data = []
        
        for node_name in sorted(current_mdp.keys()):
            node = current_mdp[node_name]
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
        return {
            'success': False,
            'error': str(e),
            'message': f'Error solving MDP: {str(e)}'
        }

def create_graph_figure(solution_data):
    """Create Plotly figure for MDP graph"""
    if not solution_data or not solution_data.get('success'):
        return go.Figure().add_annotation(
            text="Solve an MDP to see the graph visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
    
    nodes = solution_data['nodes']
    edges = solution_data['edges']
    
    # Create node positions using a simple layout
    node_names = list(nodes.keys())
    n_nodes = len(node_names)
    
    # Simple circular layout
    angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    radius = max(3, n_nodes * 0.5)
    
    node_positions = {}
    for i, name in enumerate(node_names):
        node_positions[name] = {
            'x': radius * np.cos(angles[i]),
            'y': radius * np.sin(angles[i])
        }
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    for edge in edges:
        source_pos = node_positions[edge['source']]
        target_pos = node_positions[edge['target']]
        
        # Edge line
        fig.add_trace(go.Scatter(
            x=[source_pos['x'], target_pos['x'], None],
            y=[source_pos['y'], target_pos['y'], None],
            mode='lines',
            line=dict(
                color='gold' if edge['is_policy'] else 'gray',
                width=4 if edge['is_policy'] else 2
            ),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Edge probability label
        mid_x = (source_pos['x'] + target_pos['x']) / 2
        mid_y = (source_pos['y'] + target_pos['y']) / 2
        
        fig.add_trace(go.Scatter(
            x=[mid_x],
            y=[mid_y],
            mode='text',
            text=[f"{edge['probability']:.2f}"],
            textfont=dict(size=10, color='black'),
            showlegend=False,
            hoverinfo='none'
        ))
    
    # Add nodes
    node_colors = {
        'decision': 'blue',
        'chance': 'green', 
        'terminal': 'red'
    }
    
    for node_name, node_data in nodes.items():
        pos = node_positions[node_name]
        color = node_colors.get(node_data['type'], 'gray')
        
        fig.add_trace(go.Scatter(
            x=[pos['x']],
            y=[pos['y']],
            mode='markers+text',
            marker=dict(
                size=30,
                color=color,
                line=dict(width=2, color='darkblue')
            ),
            text=[node_name],
            textfont=dict(size=12, color='white'),
            textposition='middle center',
            name=f"{node_name} (Value: {node_data['value']:.3f})",
            hovertemplate=f"<b>{node_name}</b><br>" +
                         f"Type: {node_data['type']}<br>" +
                         f"Value: {node_data['value']:.3f}<br>" +
                         f"Reward: {node_data['reward']}<br>" +
                         "<extra></extra>",
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title="MDP Graph Visualization",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20),
        height=500
    )
    
    return fig

# Layout
app.layout = dbc.Container([
    # Header
    dbc.NavbarSimple(
        brand="MDP Solver",
        brand_href="#",
        color="primary",
        dark=True,
        className="mb-3"
    ),
    
    dbc.Row([
        # Left Panel - Input and Controls
        dbc.Col([
            # Input Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5("MDP Input", className="mb-0"),
                    dbc.ButtonGroup([
                        dbc.Button("Examples", id="examples-btn", color="outline-primary", size="sm"),
                        dbc.Button("Clear", id="clear-btn", color="outline-secondary", size="sm")
                    ], size="sm")
                ], className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    dcc.Textarea(
                        id="mdp-input",
                        placeholder="""Enter your MDP definition here...

Example:
# Terminal states
Z=1
Y=-1

# Decision nodes  
A : [Z, C, Y]
A % .8

# More nodes...""",
                        style={'height': 300, 'fontFamily': 'monospace'},
                        className="form-control"
                    )
                ], className="p-0"),
                dbc.CardFooter([
                    html.Div(id="input-status", children=[
                        dbc.Badge("Ready", color="secondary", className="me-2"),
                        html.Small("Enter MDP definition to see statistics", className="text-muted")
                    ])
                ])
            ], className="mb-3"),
            
            # Parameters Section  
            dbc.Card([
                dbc.CardHeader(html.H5("Solver Parameters", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Discount Factor"),
                            dcc.Slider(
                                id="discount-factor",
                                min=0, max=1, step=0.01, value=1.0,
                                marks={0: '0.0', 0.5: '0.5', 1: '1.0'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Tolerance"),
                            dbc.Input(id="tolerance", type="number", value=0.01, step=0.001, min=0.001)
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Max Iterations"),
                            dbc.Input(id="max-iterations", type="number", value=100, min=1)
                        ], md=6),
                        dbc.Col([
                            dbc.Checklist(
                                id="minimize-check",
                                options=[{"label": "Minimize (costs)", "value": True}],
                                value=[],
                                className="mt-4"
                            )
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Button(
                        "Solve MDP", 
                        id="solve-btn", 
                        color="success", 
                        className="w-100",
                        disabled=True
                    )
                ])
            ])
        ], md=4),
        
        # Right Panel - Visualization and Results
        dbc.Col([
            # Graph Visualization
            dbc.Card([
                dbc.CardHeader([
                    html.H5("MDP Graph Visualization", className="mb-0"),
                    dbc.ButtonGroup([
                        dbc.Button("Re-layout", color="outline-primary", size="sm", disabled=True),
                        dbc.Button("Reset Zoom", color="outline-secondary", size="sm", disabled=True)
                    ], size="sm")
                ], className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    dcc.Graph(id="mdp-graph", style={'height': '500px'})
                ], className="p-0")
            ], className="mb-3"),
            
            # Results Section
            dbc.Row([
                # Optimal Policy
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Optimal Policy", className="mb-0")),
                        dbc.CardBody(id="policy-results", children=[
                            html.Div([
                                html.I(className="fas fa-route fa-2x mb-2"),
                                html.P("Solve the MDP to see the optimal policy")
                            ], className="text-center text-muted")
                        ])
                    ])
                ], md=6),
                
                # Node Values
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Node Values", className="mb-0")),
                        dbc.CardBody(id="value-results", children=[
                            html.Div([
                                html.I(className="fas fa-calculator fa-2x mb-2"),
                                html.P("Solve the MDP to see node values")
                            ], className="text-center text-muted")
                        ])
                    ])
                ], md=6)
            ])
        ], md=8)
    ]),
    
    # Examples Modal
    dbc.Modal([
        dbc.ModalHeader("Example MDPs"),
        dbc.ModalBody([
            dcc.Dropdown(
                id="examples-dropdown",
                options=load_examples(),
                placeholder="Select an example MDP..."
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Load Example", id="load-example-btn", color="primary"),
            dbc.Button("Close", id="close-examples", color="secondary")
        ])
    ], id="examples-modal", is_open=False),
    
    # Store components for state management
    dcc.Store(id="current-solution", data=None),
    dcc.Store(id="validation-result", data=None)
    
], fluid=True)

# Callbacks
@app.callback(
    Output("validation-result", "data"),
    Output("input-status", "children"),
    Output("solve-btn", "disabled"),
    Input("mdp-input", "value")
)
def validate_input(input_text):
    if not input_text or not input_text.strip():
        return None, [
            dbc.Badge("Ready", color="secondary", className="me-2"),
            html.Small("Enter MDP definition to see statistics", className="text-muted")
        ], True
    
    result = validate_mdp_input(input_text)
    
    if result['valid']:
        stats = f"{result['nodes']} nodes ({result['decision_nodes']} decision, {result['chance_nodes']} chance, {result['terminal_nodes']} terminal)"
        return result, [
            dbc.Badge("Valid", color="success", className="me-2"),
            html.Small(stats, className="text-muted")
        ], False
    else:
        return result, [
            dbc.Badge("Invalid", color="danger", className="me-2"),
            html.Small(result['message'], className="text-muted")
        ], True

@app.callback(
    Output("current-solution", "data"),
    Output("solve-btn", "children"),
    Input("solve-btn", "n_clicks"),
    State("mdp-input", "value"),
    State("discount-factor", "value"),
    State("tolerance", "value"),
    State("max-iterations", "value"),
    State("minimize-check", "value"),
    prevent_initial_call=True
)
def solve_mdp_callback(n_clicks, input_text, discount_factor, tolerance, max_iterations, minimize):
    if not n_clicks or not input_text:
        return no_update, "Solve MDP"
    
    try:
        # Show loading state
        loading_button = [
            dbc.Spinner(size="sm", className="me-2"),
            "Solving MDP..."
        ]
        
        minimize_bool = bool(minimize)
        solution = solve_mdp(input_text, discount_factor, tolerance, max_iterations, minimize_bool)
        
        return solution, "Solve MDP"
        
    except Exception as e:
        return {"success": False, "error": str(e)}, "Solve MDP"

@app.callback(
    Output("mdp-graph", "figure"),
    Input("current-solution", "data")
)
def update_graph(solution_data):
    return create_graph_figure(solution_data)

@app.callback(
    Output("policy-results", "children"),
    Output("value-results", "children"),
    Input("current-solution", "data")
)
def update_results(solution_data):
    if not solution_data or not solution_data.get('success'):
        policy_placeholder = html.Div([
            html.I(className="fas fa-route fa-2x mb-2"),
            html.P("Solve the MDP to see the optimal policy")
        ], className="text-center text-muted")
        
        value_placeholder = html.Div([
            html.I(className="fas fa-calculator fa-2x mb-2"),
            html.P("Solve the MDP to see node values")
        ], className="text-center text-muted")
        
        return policy_placeholder, value_placeholder
    
    # Policy results
    policy = solution_data.get('policy', {})
    if not policy:
        policy_content = html.P("No decision nodes in this MDP.", className="text-muted")
    else:
        policy_items = []
        for node in sorted(policy.keys()):
            policy_items.append(
                dbc.ListGroupItem([
                    html.Strong(node),
                    dbc.Badge(policy[node], color="primary", className="ms-auto")
                ], className="d-flex justify-content-between align-items-center")
            )
        policy_content = dbc.ListGroup(policy_items, flush=True)
    
    # Value results
    values = solution_data.get('values', {})
    value_items = []
    for node in sorted(values.keys()):
        value = values[node]
        color = "success" if value > 0 else "danger" if value < 0 else "secondary"
        value_items.append(
            dbc.ListGroupItem([
                html.Strong(node),
                dbc.Badge(f"{value:.3f}", color=color, className="ms-auto")
            ], className="d-flex justify-content-between align-items-center")
        )
    value_content = dbc.ListGroup(value_items, flush=True)
    
    return policy_content, value_content

@app.callback(
    Output("examples-modal", "is_open"),
    [Input("examples-btn", "n_clicks"), Input("close-examples", "n_clicks")],
    [State("examples-modal", "is_open")]
)
def toggle_examples_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("mdp-input", "value"),
    Input("load-example-btn", "n_clicks"),
    State("examples-dropdown", "value"),
    prevent_initial_call=True
)
def load_example(n_clicks, selected_example):
    if n_clicks and selected_example:
        return selected_example
    return no_update

@app.callback(
    Output("mdp-input", "value", allow_duplicate=True),
    Input("clear-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_input(n_clicks):
    if n_clicks:
        return ""
    return no_update

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=5050)
