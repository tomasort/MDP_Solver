// MDP Solver JavaScript with Plotly

// Global variables
let currentSolution = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    validateInputDebounced();
    
    // Wait a bit for Plotly to load
    setTimeout(() => {
        setupEmptyGraph();
    }, 100);
});

function setupEmptyGraph() {
    // Check if Plotly is available
    if (typeof Plotly === 'undefined') {
        console.error('Plotly is not loaded!');
        return;
    }
    
    console.log('Setting up empty graph...');
    
    // Initialize empty Plotly graph
    const layout = {
        title: 'MDP Graph Visualization',
        showlegend: false,
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { l: 20, r: 20, t: 40, b: 20 },
        height: 500,
        annotations: [{
            text: "Enter an MDP definition and solve to see the graph visualization",
            xref: "paper",
            yref: "paper",
            x: 0.5,
            y: 0.5,
            showarrow: false,
            font: { size: 16, color: "gray" }
        }]
    };
    
    try {
        Plotly.newPlot('mdpGraph', [], layout, { responsive: true });
        console.log('Empty graph initialized successfully');
    } catch (error) {
        console.error('Error initializing Plotly graph:', error);
    }
}

// Utility functions
function updateDiscountValue(value) {
    document.getElementById('discountValue').textContent = value;
}

function clearInput() {
    document.getElementById('mdpInput').value = '';
    updateInputStatus('ready', 'Enter MDP definition to see statistics');
    clearResults();
}

function showExamples() {
    let examplesModal = bootstrap.Modal.getInstance(document.getElementById('examplesModal'));
    if (!examplesModal) {
        examplesModal = new bootstrap.Modal(document.getElementById('examplesModal'));
    }
    examplesModal.show();
}

async function loadExample(filename) {
    try {
        const response = await fetch(`/example/${filename}`);
        const example = await response.json();
        document.getElementById('mdpInput').value = example.content;
        
        let examplesModal = bootstrap.Modal.getInstance(document.getElementById('examplesModal'));
        if (examplesModal) {
            examplesModal.hide();
        }
        
        validateInput();
    } catch (error) {
        alert('Failed to load example');
    }
}

// Debounced validation
let validationTimeout;
function validateInputDebounced() {
    clearTimeout(validationTimeout);
    validationTimeout = setTimeout(validateInput, 500);
}

// Add event listener to input
document.getElementById('mdpInput').addEventListener('input', validateInputDebounced);

async function validateInput() {
    const input = document.getElementById('mdpInput').value.trim();
    
    if (!input) {
        updateInputStatus('ready', 'Enter MDP definition to see statistics');
        return;
    }

    try {
        const response = await fetch('/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            const stats = `${result.nodes} nodes (${result.decision_nodes} decision, ${result.chance_nodes} chance, ${result.terminal_nodes} terminal)`;
            updateInputStatus('valid', stats);
            document.getElementById('solveBtn').disabled = false;
        } else {
            updateInputStatus('invalid', result.message);
            document.getElementById('solveBtn').disabled = true;
        }
    } catch (error) {
        updateInputStatus('invalid', 'Error validating input');
        document.getElementById('solveBtn').disabled = true;
    }
}

function updateInputStatus(status, message) {
    const badge = document.querySelector('#inputStatus .badge');
    const stats = document.getElementById('inputStats');
    
    badge.className = `badge me-2 bg-${status === 'valid' ? 'success' : status === 'invalid' ? 'danger' : 'secondary'}`;
    badge.textContent = status === 'valid' ? 'Valid' : status === 'invalid' ? 'Invalid' : 'Ready';
    stats.textContent = message;
}

async function solveMDP() {
    const input = document.getElementById('mdpInput').value.trim();
    
    if (!input) {
        alert('Please enter an MDP definition first.');
        return;
    }

    const solveBtn = document.getElementById('solveBtn');
    solveBtn.disabled = true;
    solveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving MDP...';

    try {
        const params = {
            input: input,
            discountFactor: parseFloat(document.getElementById('discountFactor').value),
            tolerance: parseFloat(document.getElementById('tolerance').value),
            maxIterations: parseInt(document.getElementById('maxIterations').value),
            minimize: document.getElementById('minimizeCheck').checked
        };

        const response = await fetch('/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        const result = await response.json();

        if (result.success) {
            currentSolution = result;
            displayResults();
            visualizeGraph();
        } else {
            alert(`Error solving MDP: ${result.error || result.message}`);
        }
    } catch (error) {
        alert(`Error solving MDP: ${error.message}`);
    } finally {
        solveBtn.disabled = false;
        solveBtn.innerHTML = '<i class="fas fa-play"></i> Solve MDP';
    }
}

function displayResults() {
    if (!currentSolution) return;

    displayPolicy();
    displayValues();
}

function displayPolicy() {
    const policy = currentSolution.policy;
    const container = document.getElementById('policyResults');

    if (Object.keys(policy).length === 0) {
        container.innerHTML = '<p class="text-muted">No decision nodes in this MDP.</p>';
        return;
    }

    let html = '';
    Object.keys(policy).sort().forEach(node => {
        html += `
            <div class="policy-item">
                <strong>${node}</strong>
                <span class="badge bg-primary">${policy[node]}</span>
            </div>
        `;
    });

    container.innerHTML = html;
}

function displayValues() {
    const values = currentSolution.values;
    const container = document.getElementById('valueResults');

    let html = '';
    Object.keys(values).sort().forEach(node => {
        const value = values[node];
        const valueClass = value > 0 ? 'value-positive' : value < 0 ? 'value-negative' : 'value-zero';

        html += `
            <div class="value-item ${valueClass}">
                <strong>${node}</strong>
                <span class="badge bg-secondary">${value.toFixed(3)}</span>
            </div>
        `;
    });

    container.innerHTML = html;
}

function clearResults() {
    document.getElementById('policyResults').innerHTML = `
        <div class="text-center text-muted">
            <i class="fas fa-route fa-2x mb-2"></i>
            <p>Solve the MDP to see the optimal policy</p>
        </div>
    `;

    document.getElementById('valueResults').innerHTML = `
        <div class="text-center text-muted">
            <i class="fas fa-calculator fa-2x mb-2"></i>
            <p>Solve the MDP to see node values</p>
        </div>
    `;

    document.getElementById('graphPlaceholder').style.display = 'flex';
    currentSolution = null;
    clearGraph();
}

function visualizeGraph() {
    console.log('visualizeGraph called', currentSolution);
    
    if (!currentSolution || !currentSolution.nodes || !currentSolution.edges) {
        console.log('No solution data available');
        return;
    }

    console.log('Hiding placeholder and showing graph');
    document.getElementById('graphPlaceholder').style.display = 'none';

    const nodes = currentSolution.nodes;
    const edges = currentSolution.edges;
    
    // Create node positions using a simple circular layout
    const nodeNames = Object.keys(nodes);
    const nNodes = nodeNames.length;
    
    // Simple circular layout
    const nodePositions = {};
    const radius = Math.max(3, nNodes * 0.5);
    
    for (let i = 0; i < nNodes; i++) {
        const angle = (2 * Math.PI * i) / nNodes;
        nodePositions[nodeNames[i]] = {
            x: radius * Math.cos(angle),
            y: radius * Math.sin(angle)
        };
    }
    
    const traces = [];
    
    // Add edges as lines
    const edgeXs = [];
    const edgeYs = [];
    const edgeLabels = [];
    
    edges.forEach(edge => {
        const sourcePos = nodePositions[edge.source];
        const targetPos = nodePositions[edge.target];
        
        // Add edge line
        edgeXs.push(sourcePos.x, targetPos.x, null);
        edgeYs.push(sourcePos.y, targetPos.y, null);
        
        // Add probability label at midpoint
        const midX = (sourcePos.x + targetPos.x) / 2;
        const midY = (sourcePos.y + targetPos.y) / 2;
        
        traces.push({
            x: [midX],
            y: [midY],
            mode: 'text',
            text: [edge.probability.toFixed(2)],
            textfont: { size: 12, color: 'black' },
            showlegend: false,
            hoverinfo: 'none'
        });
    });
    
    // Add all edges as one trace
    traces.push({
        x: edgeXs,
        y: edgeYs,
        mode: 'lines',
        line: { color: 'gray', width: 2 },
        showlegend: false,
        hoverinfo: 'none'
    });
    
    // Add policy edges (highlighted)
    const policyEdgeXs = [];
    const policyEdgeYs = [];
    
    edges.forEach(edge => {
        if (edge.is_policy) {
            const sourcePos = nodePositions[edge.source];
            const targetPos = nodePositions[edge.target];
            policyEdgeXs.push(sourcePos.x, targetPos.x, null);
            policyEdgeYs.push(sourcePos.y, targetPos.y, null);
        }
    });
    
    if (policyEdgeXs.length > 0) {
        traces.push({
            x: policyEdgeXs,
            y: policyEdgeYs,
            mode: 'lines',
            line: { color: 'gold', width: 4 },
            showlegend: false,
            hoverinfo: 'none'
        });
    }
    
    // Add nodes by type
    const nodeColors = {
        'decision': '#0d6efd',
        'chance': '#198754',
        'terminal': '#dc3545'
    };
    
    Object.keys(nodeColors).forEach(nodeType => {
        const nodeX = [];
        const nodeY = [];
        const nodeText = [];
        const nodeHover = [];
        
        Object.values(nodes).forEach(node => {
            if (node.type === nodeType) {
                const pos = nodePositions[node.name];
                nodeX.push(pos.x);
                nodeY.push(pos.y);
                nodeText.push(node.name);
                nodeHover.push(
                    `<b>${node.name}</b><br>` +
                    `Type: ${node.type}<br>` +
                    `Value: ${node.value.toFixed(3)}<br>` +
                    `Reward: ${node.reward}`
                );
            }
        });
        
        if (nodeX.length > 0) {
            traces.push({
                x: nodeX,
                y: nodeY,
                mode: 'markers+text',
                marker: {
                    size: 30,
                    color: nodeColors[nodeType],
                    line: { width: 2, color: 'white' }
                },
                text: nodeText,
                textfont: { size: 12, color: 'white' },
                textposition: 'middle center',
                hovertemplate: '%{hovertext}<extra></extra>',
                hovertext: nodeHover,
                name: nodeType.charAt(0).toUpperCase() + nodeType.slice(1),
                showlegend: true
            });
        }
    });
    
    const layout = {
        title: 'MDP Graph Visualization',
        showlegend: true,
        legend: { x: 0, y: 1 },
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { l: 20, r: 20, t: 40, b: 20 },
        height: 500,
        hovermode: 'closest'
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false
    };
    
    console.log('Creating Plotly graph with traces:', traces.length);
    
    try {
        Plotly.newPlot('mdpGraph', traces, layout, config);
        console.log('Graph created successfully');
    } catch (error) {
        console.error('Error creating Plotly graph:', error);
    }
}

function relayoutGraph() {
    // Re-trigger visualization with current solution
    if (currentSolution) {
        visualizeGraph();
    }
}

function resetZoom() {
    Plotly.relayout('mdpGraph', {
        'xaxis.autorange': true,
        'yaxis.autorange': true
    });
}

function clearGraph() {
    setupEmptyGraph();
}
