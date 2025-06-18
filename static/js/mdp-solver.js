// MDP Solver Web Interface

class MDPSolver {
    constructor() {
        this.resetMDPData();
        this.currentResults = null;
        
        this.initializeEventListeners();
        this.initializeTooltips();
        this.updateDiscountDisplay();
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
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileUpload(e));
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
    }

    // Show placeholder content in results section
    showPlaceholderResults() {
        // Restore placeholder in policy table
        const policyTbody = document.getElementById('policyTableBody');
        policyTbody.innerHTML = `
            <tr class="placeholder-row">
                <td colspan="2" class="text-center text-muted py-4">
                    <i class="fas fa-play-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>
                    Click "Solve MDP" to see the optimal policy
                </td>
            </tr>
        `;

        // Restore placeholder in values table
        const valuesTbody = document.getElementById('valuesTableBody');
        valuesTbody.innerHTML = `
            <tr class="placeholder-row">
                <td colspan="2" class="text-center text-muted py-4">
                    <i class="fas fa-calculator fa-3x mb-3 d-block" style="opacity: 0.3;"></i>
                    State values will appear here after solving
                </td>
            </tr>
        `;

        // Restore placeholder statistics
        const statsElement = document.getElementById('solutionStats');
        const alertElement = document.getElementById('solutionStatsAlert');
        alertElement.className = 'alert alert-secondary';
        statsElement.textContent = 'Define an MDP and click "Solve MDP" to see solution statistics';
    }

    // Populate the policy table
    populatePolicyTable(policy) {
        const tbody = document.getElementById('policyTableBody');
        tbody.innerHTML = '';

        // Sort states alphabetically for consistent display
        const sortedStates = Object.keys(policy).sort();
        
        sortedStates.forEach(state => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = state;
            row.insertCell(1).textContent = policy[state];
        });
    }

    // Populate the values table
    populateValuesTable(values) {
        const tbody = document.getElementById('valuesTableBody');
        tbody.innerHTML = '';

        // Sort states alphabetically for consistent display
        const sortedStates = Object.keys(values).sort();
        
        sortedStates.forEach(state => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = state;
            row.insertCell(1).textContent = Number(values[state]).toFixed(3);
        });
    }

    // Update solution statistics
    updateSolutionStats(result) {
        const statsElement = document.getElementById('solutionStats');
        const alertElement = document.getElementById('solutionStatsAlert');
        const iterations = result.iterations || 'N/A';
        const converged = result.converged ? 'Yes' : 'No';
        
        // Change alert style to info when results are available
        alertElement.className = 'alert alert-info';
        
        statsElement.innerHTML = `
            Iterations: <strong>${iterations}</strong> | 
            Converged: <strong>${converged}</strong> | 
            States: <strong>${Object.keys(result.values).length}</strong>
        `;
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
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const result = await this.makeRequest('/api/upload', {
                method: 'POST',
                headers: {}, // Remove Content-Type to let browser set it for FormData
                body: formData
            });

            if (result.success) {
                document.getElementById('textEditor').value = result.content;
                this.parseTextInput();
                this.showAlert('File uploaded successfully!', 'success');
            } else {
                this.showAlert(`Upload error: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Upload error: ${error.message}`, 'danger');
        } finally {
            event.target.value = ''; // Clear file input
        }
    }

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
}

// Global functions for HTML event handlers
window.loadExample = function(exampleName) {
    window.mdpSolver.loadExample(exampleName);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.mdpSolver = new MDPSolver();
    console.log('MDP Solver initialized');
    
    // Load available examples
    window.mdpSolver.loadAvailableExamples();
});
