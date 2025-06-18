// MDP Solver Web Interface

class MDPSolver {
    constructor() {
        this.resetMDPData();
        this.currentResults = null;
        
        this.initializeEventListeners();
        this.initializeTooltips();
        this.updateDiscountDisplay();
        
        // Load available examples
        this.loadAvailableExamples();
    }

    // Initialize MDP data structure
    resetMDPData() {
        this.mdpData = {
            states: {},
            transitions: {}
        };
    }

    // Get configuration from UI elements
    getConfiguration() {
        return {
            discount_factor: parseFloat(document.getElementById('discountFactor').value),
            tolerance: parseFloat(document.getElementById('tolerance').value),
            minimize: document.getElementById('minimize').checked
        };
    }

    // Common HTTP request handler
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        return await response.json();
    }

    initializeEventListeners() {
        // Parameter controls
        document.getElementById('discountFactor').addEventListener('input', () => this.updateDiscountDisplay());

        // Action buttons
        document.getElementById('solveBtn').addEventListener('click', () => this.solveMDP());
        document.getElementById('validateBtn').addEventListener('click', () => this.validateMDP());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearAll());

        // File operations
        document.getElementById('textEditor').addEventListener('input', () => this.parseTextInput());
    }

    initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => new bootstrap.Tooltip(element));
    }

    updateDiscountDisplay() {
        const value = document.getElementById('discountFactor').value;
        document.getElementById('discountValue').textContent = value;
    }

    // Solve the MDP using the backend API
    async solveMDP() {
        const textInput = document.getElementById('textEditor').value.trim();
        
        if (!textInput) {
            this.showAlert('Please enter MDP definition in the text editor.', 'warning');
            return;
        }
        
        try {
            const requestData = {
                text_input: textInput,
                ...this.getConfiguration()
            };

            const result = await this.makeRequest('/api/solve', {
                body: JSON.stringify(requestData)
            });

            this.handleSolveResult(result);
        } catch (error) {
            this.showAlert(`Network error: ${error.message}`, 'danger');
            console.error('Network error:', error);
        }
    }

    // Handle the result from MDP solving
    handleSolveResult(result) {
        if (result.success) {
            this.currentResults = result;
            this.showAlert('MDP solved successfully! Results displayed below.', 'success');
            this.displayResults(result);
            this.logSolution(result);
        } else {
            this.showAlert(`Error: ${result.error}`, 'danger');
            console.error('Solver error:', result);
            this.showPlaceholderResults();
        }
    }

    // Display results in the UI
    displayResults(result) {
        this.populatePolicyTable(result.policy);
        this.populateValuesTable(result.values);
        this.updateSolutionStats(result);
        
        // Display graph if graph data is available
        if (result.graph) {
            this.displayGraph(result.graph);
        }
    }

    // Show placeholder content in results section
    showPlaceholderResults() {
        // Restore placeholder in policy table (both desktop and mobile)
        const policyTbodies = ['policyTableBody', 'policyTableBody-mobile'];
        policyTbodies.forEach(id => {
            const tbody = document.getElementById(id);
            if (tbody) {
                tbody.innerHTML = `
                    <tr class="placeholder-row">
                        <td colspan="2" class="text-center text-muted py-4">
                            <i class="fas fa-play-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>
                            Click "Solve MDP" to see the optimal policy
                        </td>
                    </tr>
                `;
            }
        });

        // Restore placeholder in values table (both desktop and mobile)
        const valuesTbodies = ['valuesTableBody', 'valuesTableBody-mobile'];
        valuesTbodies.forEach(id => {
            const tbody = document.getElementById(id);
            if (tbody) {
                tbody.innerHTML = `
                    <tr class="placeholder-row">
                        <td colspan="2" class="text-center text-muted py-4">
                            <i class="fas fa-calculator fa-3x mb-3 d-block" style="opacity: 0.3;"></i>
                            State values will appear here after solving
                        </td>
                    </tr>
                `;
            }
        });

        // Restore placeholder statistics (both desktop and mobile)
        const statsElements = ['solutionStats', 'solutionStats-mobile'];
        const alertElements = ['solutionStatsAlert', 'solutionStatsAlert-mobile'];
        
        statsElements.forEach((id, index) => {
            const statsElement = document.getElementById(id);
            const alertElement = document.getElementById(alertElements[index]);
            if (statsElement && alertElement) {
                alertElement.className = 'alert alert-secondary';
                statsElement.textContent = 'Define an MDP and click "Solve MDP" to see solution statistics';
            }
        });
        
        // Hide graph sections (both desktop and mobile)
        const graphSections = ['graphSection', 'graphSection-mobile'];
        graphSections.forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                section.style.display = 'none';
            }
        });
    }

    // Populate the policy table
    populatePolicyTable(policy) {
        const tbodies = ['policyTableBody', 'policyTableBody-mobile'];
        
        tbodies.forEach(id => {
            const tbody = document.getElementById(id);
            if (tbody) {
                tbody.innerHTML = '';

                // Sort states alphabetically for consistent display
                const sortedStates = Object.keys(policy).sort();
                
                sortedStates.forEach(state => {
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = state;
                    row.insertCell(1).textContent = policy[state];
                });
            }
        });
    }

    // Populate the values table
    populateValuesTable(values) {
        const tbodies = ['valuesTableBody', 'valuesTableBody-mobile'];
        
        tbodies.forEach(id => {
            const tbody = document.getElementById(id);
            if (tbody) {
                tbody.innerHTML = '';

                // Sort states alphabetically for consistent display
                const sortedStates = Object.keys(values).sort();
                
                sortedStates.forEach(state => {
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = state;
                    row.insertCell(1).textContent = Number(values[state]).toFixed(3);
                });
            }
        });
    }

    // Update solution statistics
    updateSolutionStats(result) {
        const statsElements = ['solutionStats', 'solutionStats-mobile'];
        const alertElements = ['solutionStatsAlert', 'solutionStatsAlert-mobile'];
        const iterations = result.iterations || 'N/A';
        const converged = result.converged ? 'Yes' : 'No';
        
        statsElements.forEach((id, index) => {
            const statsElement = document.getElementById(id);
            const alertElement = document.getElementById(alertElements[index]);
            
            if (statsElement && alertElement) {
                // Change alert style to info when results are available
                alertElement.className = 'alert alert-info';
                
                statsElement.innerHTML = `
                    Iterations: <strong>${iterations}</strong> | 
                    Converged: <strong>${converged}</strong> | 
                    States: <strong>${Object.keys(result.values).length}</strong>
                `;
            }
        });
    }

    // Log the solution to console in a formatted way
    logSolution(result) {
        console.log('=== MDP SOLUTION ===');
        console.log('Policy:', result.policy);
        console.log('Values:', result.values);
        console.log('Iterations:', result.iterations);
        console.log('Converged:', result.converged);
    }

    // Validate MDP structure
    async validateMDP() {
        try {
            const result = await this.makeRequest('/api/validate', {
                body: JSON.stringify({
                    states: this.mdpData.states,
                    transitions: this.mdpData.transitions
                })
            });

            this.handleValidationResult(result);
        } catch (error) {
            this.showAlert(`Validation error: ${error.message}`, 'danger');
        }
    }

    // Handle validation results
    handleValidationResult(result) {
        if (result.valid) {
            this.showAlert('MDP structure is valid!', 'success');
        } else {
            const message = this.formatValidationMessage(result);
            this.showAlert(message, 'warning');
        }
    }

    // Format validation error and warning messages
    formatValidationMessage(result) {
        let message = 'Validation failed:\\n';
        result.errors.forEach(error => message += `• ${error}\\n`);
        
        if (result.warnings && result.warnings.length > 0) {
            message += '\\nWarnings:\\n';
            result.warnings.forEach(warning => message += `• ${warning}\\n`);
        }
        
        return message;
    }

    // Clear all data and reset UI
    clearAll() {
        if (confirm('Are you sure you want to clear all data?')) {
            this.resetMDPData();
            this.currentResults = null;
            document.getElementById('textEditor').value = '';
            this.showPlaceholderResults();
            this.showAlert('All data cleared.', 'info');
        }
    }

    // Load example MDP from the server
    async loadExample(exampleName) {
        try {
            // First get example metadata
            const examples = await this.makeRequest('/api/examples', { method: 'GET' });
            
            if (examples[exampleName]) {
                const example = examples[exampleName];
                
                // Then get the content of the example file
                const result = await this.makeRequest(`/api/examples/${exampleName}/content`, { method: 'GET' });
                
                if (result.success) {
                    // Load the example content
                    this.loadExampleData(example, result.content);
                    this.showAlert(`Loaded example: ${example.name}`, 'success');
                } else {
                    this.showAlert(`Error loading example content: ${result.error}`, 'danger');
                }
            } else {
                this.showAlert(`Example not found: ${exampleName}`, 'warning');
            }
        } catch (error) {
            this.showAlert(`Error loading example: ${error.message}`, 'danger');
        }
    }

    // Load example data into the interface
    loadExampleData(example, content) {
        // Update UI controls
        document.getElementById('discountFactor').value = example.discount_factor;
        document.getElementById('tolerance').value = example.tolerance;
        document.getElementById('minimize').checked = example.minimize || false;
        this.updateDiscountDisplay();
        
        // Update text editor with content from file
        document.getElementById('textEditor').value = content;
        
        // Parse the text to populate mdpData
        this.parseTextInput();
    }

    // Load available examples from the server and populate the UI
    async loadAvailableExamples() {
        try {
            const examples = await this.makeRequest('/api/examples', { method: 'GET' });
            const container = document.getElementById('examplesContainer');
            
            // Clear loading message
            container.innerHTML = '';
            
            // Sort examples by name
            const sortedExamples = Object.entries(examples)
                .map(([id, example]) => ({ id, ...example }))
                .sort((a, b) => a.name.localeCompare(b.name));
                
            // Add buttons for each example
            sortedExamples.forEach(example => {
                const button = document.createElement('button');
                button.className = 'btn btn-outline-primary btn-sm';
                button.onclick = () => window.loadExample(example.id);
                button.innerHTML = `
                    ${example.name}
                    <small class="d-block text-muted">${example.description}</small>
                `;
                container.appendChild(button);
            });
            
            if (sortedExamples.length === 0) {
                container.innerHTML = '<div class="text-center text-muted py-2">No examples available</div>';
            }
            
        } catch (error) {
            const container = document.getElementById('examplesContainer');
            container.innerHTML = '<div class="text-center text-danger py-2">Failed to load examples</div>';
            console.error('Failed to load examples:', error);
        }
    }

    // Handle file upload
    // Parse text input from the editor into MDP data structure
    parseTextInput() {
        const text = document.getElementById('textEditor').value;
        const lines = text.split('\\n').filter(line => line.trim());
        
        this.resetMDPData();

        try {
            lines.forEach(line => this.parseLine(line.trim()));
        } catch (error) {
            console.error('Parsing error:', error);
        }
    }

    // Parse a single line of MDP definition
    parseLine(line) {
        if (!line) return;

        if (line.includes('=')) {
            this.parseRewardLine(line);
        } else if (line.includes(':')) {
            this.parseEdgeLine(line);
        } else if (line.includes('%')) {
            this.parseProbabilityLine(line);
        }
    }

    // Parse reward line: state = reward
    parseRewardLine(line) {
        const [stateName, reward] = line.split('=').map(s => s.trim());
        this.ensureStateExists(stateName);
        this.mdpData.states[stateName].reward = parseFloat(reward);
    }

    // Parse edge line: state : [edge1, edge2]
    parseEdgeLine(line) {
        const [stateName, edgesStr] = line.split(':').map(s => s.trim());
        const edges = edgesStr.replace(/[\\[\\]]/g, '').split(',').map(s => s.trim());
        this.ensureStateExists(stateName);
        this.mdpData.states[stateName].edges = edges;
    }

    // Parse probability line: state % p1 p2 p3
    parseProbabilityLine(line) {
        const [stateName, probsStr] = line.split('%').map(s => s.trim());
        const probs = probsStr.split(/\\s+/).map(p => parseFloat(p.trim()));
        this.mdpData.transitions[stateName] = probs;
    }

    // Ensure a state exists in the data structure
    ensureStateExists(stateName) {
        if (!this.mdpData.states[stateName]) {
            this.mdpData.states[stateName] = { reward: 0, type: 'decision', edges: [] };
        }
    }

    // These methods have been removed since we now load examples directly from files:
    // - updateTextEditor()
    // - generateRewardLines()
    // - generateEdgeLines()
    // - generateProbabilityLines()

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
                ${message.replace(/\\n/g, '<br>')}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    // Display MDP graph using D3.js
    displayGraph(graphData) {
        // Show the graph sections (both desktop and mobile)
        const graphSections = ['graphSection', 'graphSection-mobile'];
        const graphContainers = ['mdpGraph', 'mdpGraph-mobile'];
        
        graphSections.forEach((sectionId, index) => {
            const section = document.getElementById(sectionId);
            const containerId = graphContainers[index];
            
            if (section) {
                section.style.display = 'block';
                
                // Clear any existing graph
                d3.select(`#${containerId}`).selectAll("*").remove();
                
                const container = document.getElementById(containerId);
                if (container) {
                    const width = container.clientWidth;
                    const height = 400;
                    
                    // Create SVG
                    const svg = d3.select(`#${containerId}`)
                        .append("svg")
                        .attr("width", width)
                        .attr("height", height);
                    
                    // Define arrow markers for edges
                    svg.append("defs").selectAll("marker")
                        .data(["optimal", "alternative"])
                        .enter().append("marker")
                        .attr("id", d => `arrow-${d}-${index}`)
                        .attr("viewBox", "0 -5 10 10")
                        .attr("refX", 20)
                        .attr("refY", 0)
                        .attr("markerWidth", 6)
                        .attr("markerHeight", 6)
                        .attr("orient", "auto")
                        .append("path")
                        .attr("d", "M0,-5L10,0L0,5")
                        .attr("fill", d => d === "optimal" ? "#2196F3" : "#E0E0E0");
                    
                    // Create force simulation
                    this.createGraphVisualization(svg, graphData, width, height, index);
                }
            }
        });
    }

    createGraphVisualization(svg, graphData, width, height, index) {
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(25));
        
        // Create links/edges
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graphData.edges)
            .enter().append("line")
            .attr("stroke", d => d.is_optimal ? "#2196F3" : "#E0E0E0")
            .attr("stroke-width", d => d.is_optimal ? 3 : 1)
            .attr("marker-end", d => `url(#arrow-${d.is_optimal ? 'optimal' : 'alternative'}-${index})`);
        
        // Create nodes
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(graphData.nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", (event, d) => this.dragstarted(event, d, simulation))
                .on("drag", (event, d) => this.dragged(event, d))
                .on("end", (event, d) => this.dragended(event, d, simulation)));
        
        // Add circles for nodes
        node.append("circle")
            .attr("r", 15)
            .attr("fill", d => this.getNodeColor(d.value))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2);
        
        // Add labels for nodes
        node.append("text")
            .attr("dx", 0)
            .attr("dy", 4)
            .attr("text-anchor", "middle")
            .attr("font-size", "10px")
            .attr("font-weight", "bold")
            .attr("fill", "#fff")
            .text(d => d.name.length > 6 ? d.name.substring(0, 6) + "..." : d.name);
        
        // Add tooltips
        node.append("title")
            .text(d => `State: ${d.name}\nValue: ${d.value.toFixed(3)}\nReward: ${d.reward}`);
        
        // Add edge labels for probabilities
        const edgeLabels = svg.append("g")
            .attr("class", "edge-labels")
            .selectAll("text")
            .data(graphData.edges)
            .enter().append("text")
            .attr("font-size", "10px")
            .attr("fill", "#666")
            .attr("text-anchor", "middle")
            .text(d => d.probability.toFixed(2));
        
        // Update positions on simulation tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("transform", d => `translate(${d.x},${d.y})`);
            
            edgeLabels
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2);
        });
    }
    
    // Get node color based on value
    getNodeColor(value) {
        if (value > 0) return "#4CAF50"; // Green for positive
        if (value < 0) return "#f44336"; // Red for negative
        return "#9E9E9E"; // Gray for zero
    }
    
    // Drag event handlers for D3 simulation
    dragstarted(event, d, simulation) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    dragended(event, d, simulation) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Global functions for HTML event handlers
window.loadExample = function(exampleName) {
    window.mdpSolver.loadExample(exampleName);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.mdpSolver = new MDPSolver();
});
