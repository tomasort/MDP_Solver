// Main JavaScript for MDP Solver Web UI

class MDPSolverUI {
    constructor() {
        this.currentSolution = null;
        this.examples = [];
        this.graphManager = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExamples();
        this.initializeCodeMirror();
    }
    
    initializeElements() {
        this.elements = {
            mdpInput: document.getElementById('mdpInput'),
            inputStatus: document.getElementById('inputStatus'),
            inputStats: document.getElementById('inputStats'),
            discountFactor: document.getElementById('discountFactor'),
            discountValue: document.getElementById('discountValue'),
            tolerance: document.getElementById('tolerance'),
            maxIterations: document.getElementById('maxIterations'),
            minimizeCheck: document.getElementById('minimizeCheck'),
            solveBtn: document.getElementById('solveBtn'),
            loadExampleBtn: document.getElementById('loadExampleBtn'),
            clearBtn: document.getElementById('clearBtn'),
            layoutBtn: document.getElementById('layoutBtn'),
            zoomResetBtn: document.getElementById('zoomResetBtn'),
            policyResults: document.getElementById('policyResults'),
            valueResults: document.getElementById('valueResults'),
            graphPlaceholder: document.getElementById('graphPlaceholder'),
            examplesList: document.getElementById('examplesList')
        };
    }
    
    initializeCodeMirror() {
        // Initialize CodeMirror for syntax highlighting
        this.codeMirror = CodeMirror.fromTextArea(this.elements.mdpInput, {
            mode: 'text/plain',
            theme: 'default',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 2,
            tabSize: 2
        });
        
        this.codeMirror.on('change', () => {
            this.debounceValidation();
        });
    }
    
    bindEvents() {
        // Parameter controls
        this.elements.discountFactor.addEventListener('input', (e) => {
            this.elements.discountValue.textContent = e.target.value;
        });
        
        // Button events
        this.elements.solveBtn.addEventListener('click', () => this.solveMDP());
        this.elements.loadExampleBtn.addEventListener('click', () => this.showExamples());
        this.elements.clearBtn.addEventListener('click', () => this.clearInput());
        this.elements.layoutBtn.addEventListener('click', () => this.relayoutGraph());
        this.elements.zoomResetBtn.addEventListener('click', () => this.resetZoom());
        
        // Input validation
        this.debounceValidation = this.debounce(() => this.validateInput(), 500);
    }
    
    async loadExamples() {
        try {
            const response = await fetch('/api/examples');
            this.examples = await response.json();
        } catch (error) {
            console.error('Failed to load examples:', error);
        }
    }
    
    showExamples() {
        this.elements.examplesList.innerHTML = '';
        
        this.examples.forEach((example, index) => {
            const exampleCard = document.createElement('div');
            exampleCard.className = 'col-md-6 mb-3';
            exampleCard.innerHTML = `
                <div class="card example-card h-100" data-index="${index}">
                    <div class="card-body">
                        <h6 class="card-title">${example.name}</h6>
                        <p class="card-text text-muted small">${example.description}</p>
                        <button class="btn btn-primary btn-sm">Load Example</button>
                    </div>
                </div>
            `;
            
            exampleCard.addEventListener('click', () => {
                this.loadExample(index);
                bootstrap.Modal.getInstance(document.getElementById('examplesModal')).hide();
            });
            
            this.elements.examplesList.appendChild(exampleCard);
        });
        
        new bootstrap.Modal(document.getElementById('examplesModal')).show();
    }
    
    loadExample(index) {
        if (index >= 0 && index < this.examples.length) {
            this.codeMirror.setValue(this.examples[index].content);
            this.validateInput();
        }
    }
    
    clearInput() {
        this.codeMirror.setValue('');
        this.updateInputStatus('ready', 'Enter MDP definition to see statistics');
        this.clearResults();
    }
    
    async validateInput() {
        const input = this.codeMirror ? this.codeMirror.getValue().trim() : this.elements.mdpInput.value.trim();
        
        if (!input) {
            this.updateInputStatus('ready', 'Enter MDP definition to see statistics');
            return;
        }
        
        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input })
            });
            
            const result = await response.json();
            
            if (result.valid) {
                const stats = `${result.nodes} nodes (${result.decision_nodes} decision, ${result.chance_nodes} chance, ${result.terminal_nodes} terminal)`;
                this.updateInputStatus('valid', stats);
                this.elements.solveBtn.disabled = false;
            } else {
                this.updateInputStatus('invalid', result.message);
                this.elements.solveBtn.disabled = true;
            }
        } catch (error) {
            this.updateInputStatus('invalid', 'Error validating input');
            this.elements.solveBtn.disabled = true;
        }
    }
    
    updateInputStatus(status, message) {
        const statusBadge = this.elements.inputStatus.querySelector('.badge');
        const statsText = this.elements.inputStats;
        
        statusBadge.className = `badge me-2 status-${status}`;
        
        switch (status) {
            case 'valid':
                statusBadge.textContent = 'Valid';
                break;
            case 'invalid':
                statusBadge.textContent = 'Invalid';
                break;
            default:
                statusBadge.textContent = 'Ready';
        }
        
        statsText.textContent = message;
    }
    
    async solveMDP() {
        const input = this.codeMirror ? this.codeMirror.getValue().trim() : this.elements.mdpInput.value.trim();
        
        if (!input) {
            alert('Please enter an MDP definition first.');
            return;
        }
        
        // Show loading modal
        const loadingModalElement = document.getElementById('loadingModal');
        const loadingModal = new bootstrap.Modal(loadingModalElement);
        loadingModal.show();
        
        // Disable solve button
        this.elements.solveBtn.disabled = true;
        this.elements.solveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving...';
        
        try {
            const params = {
                input: input,
                discountFactor: parseFloat(this.elements.discountFactor.value),
                tolerance: parseFloat(this.elements.tolerance.value),
                maxIterations: parseInt(this.elements.maxIterations.value),
                minimize: this.elements.minimizeCheck.checked
            };
            
            console.log('Sending solve request with params:', params);
            
            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            console.log('Received response:', response);
            const result = await response.json();
            console.log('Parsed result:', result);
            
            if (result.success) {
                this.currentSolution = result;
                this.displayResults();
                this.visualizeGraph();
            } else {
                alert(`Error solving MDP: ${result.error || result.message}`);
            }
        } catch (error) {
            console.error('Error solving MDP:', error);
            alert(`Error solving MDP: ${error.message}`);
        } finally {
            // Hide loading modal - force hide it
            try {
                loadingModal.hide();
                // Force remove backdrop if it exists
                setTimeout(() => {
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                    // Ensure body class is removed
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 100);
            } catch (e) {
                console.error('Error hiding modal:', e);
            }
            
            // Reset solve button
            this.elements.solveBtn.disabled = false;
            this.elements.solveBtn.innerHTML = '<i class="fas fa-play"></i> Solve MDP';
        }
    }
    
    displayResults() {
        if (!this.currentSolution) return;
        
        this.displayPolicy();
        this.displayValues();
    }
    
    displayPolicy() {
        const policy = this.currentSolution.policy;
        const policyContainer = this.elements.policyResults;
        
        if (Object.keys(policy).length === 0) {
            policyContainer.innerHTML = '<p class="text-muted">No decision nodes in this MDP.</p>';
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
        
        policyContainer.innerHTML = html;
    }
    
    displayValues() {
        const values = this.currentSolution.values;
        const valuesContainer = this.elements.valueResults;
        
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
        
        valuesContainer.innerHTML = html;
    }
    
    visualizeGraph() {
        if (!this.currentSolution) {
            console.error('No solution available for visualization');
            return;
        }
        
        console.log('Visualizing graph with data:', this.currentSolution);
        
        // Hide placeholder
        this.elements.graphPlaceholder.style.display = 'none';
        
        // Initialize graph manager if not exists
        if (!this.graphManager) {
            console.log('Creating new GraphManager');
            this.graphManager = new GraphManager('mdpGraph');
        }
        
        // Check if we have the required data
        if (!this.currentSolution.nodes || !this.currentSolution.edges) {
            console.error('Missing nodes or edges data:', {
                nodes: this.currentSolution.nodes,
                edges: this.currentSolution.edges
            });
            return;
        }
        
        // Render the graph
        console.log('Rendering graph with nodes:', Object.keys(this.currentSolution.nodes).length, 'edges:', this.currentSolution.edges.length);
        this.graphManager.renderGraph(this.currentSolution.nodes, this.currentSolution.edges);
    }
    
    relayoutGraph() {
        if (this.graphManager) {
            this.graphManager.relayout();
        }
    }
    
    resetZoom() {
        if (this.graphManager) {
            this.graphManager.resetZoom();
        }
    }
    
    clearResults() {
        this.elements.policyResults.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-route fa-2x mb-2"></i>
                <p>Solve the MDP to see the optimal policy</p>
            </div>
        `;
        
        this.elements.valueResults.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-calculator fa-2x mb-2"></i>
                <p>Solve the MDP to see node values</p>
            </div>
        `;
        
        this.elements.graphPlaceholder.style.display = 'flex';
        this.currentSolution = null;
        
        if (this.graphManager) {
            this.graphManager.clear();
        }
    }
    
    // Utility function for debouncing
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MDPSolverUI();
});
