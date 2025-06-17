// Graph visualization using D3.js for MDP Solver

class GraphManager {
    constructor(svgId) {
        this.svg = d3.select(`#${svgId}`);
        this.container = this.svg.node().parentNode;
        this.width = 0;
        this.height = 0;
        
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.setupSVG();
        this.updateDimensions();
        
        // Listen for window resize
        window.addEventListener('resize', () => {
            setTimeout(() => this.updateDimensions(), 100);
        });
    }
    
    setupSVG() {
        this.svg.call(this.zoom);
        
        // Create main group for all elements
        this.g = this.svg.append('g');
        
        // Define arrow markers
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#6c757d');
        
        // Define policy arrow marker
        this.svg.select('defs').append('marker')
            .attr('id', 'policyArrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#ffc107');
    }
    
    updateDimensions() {
        const rect = this.container.getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        
        this.svg
            .attr('width', this.width)
            .attr('height', this.height);
    }
    
    renderGraph(nodesData, edgesData) {
        console.log('GraphManager: Starting to render graph');
        console.log('GraphManager: Nodes data:', nodesData);
        console.log('GraphManager: Edges data:', edgesData);
        
        if (!nodesData || !edgesData) {
            console.error('GraphManager: Missing nodes or edges data');
            return;
        }
        
        if (typeof d3 === 'undefined') {
            console.error('GraphManager: D3.js is not loaded');
            return;
        }
        
        this.updateDimensions();
        this.prepareData(nodesData, edgesData);
        this.createSimulation();
        this.drawGraph();
        
        console.log('GraphManager: Graph rendering completed');
    }
    
    prepareData(nodesData, edgesData) {
        // Convert nodes data
        this.nodes = Object.values(nodesData).map(node => ({
            id: node.name,
            name: node.name,
            value: node.value,
            reward: node.reward,
            type: node.type,
            success_rate: node.success_rate,
            x: Math.random() * this.width,
            y: Math.random() * this.height
        }));
        
        // Convert edges data
        this.links = edgesData.map(edge => ({
            source: edge.source,
            target: edge.target,
            probability: edge.probability,
            is_policy: edge.is_policy
        }));
    }
    
    createSimulation() {
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links)
                .id(d => d.id)
                .distance(100)
                .strength(0.5))
            .force('charge', d3.forceManyBody()
                .strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide()
                .radius(35))
            .alpha(1)
            .alphaDecay(0.01);
    }
    
    drawGraph() {
        // Clear previous graph
        this.g.selectAll('*').remove();
        
        // Draw links first (so they appear behind nodes)
        this.linkElements = this.g.selectAll('.edge-line')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', d => `edge-line ${d.is_policy ? 'edge-policy' : ''}`)
            .attr('marker-end', d => d.is_policy ? 'url(#policyArrowhead)' : 'url(#arrowhead)');
        
        // Draw link labels
        this.linkLabels = this.g.selectAll('.edge-label')
            .data(this.links)
            .enter()
            .append('text')
            .attr('class', 'edge-label')
            .text(d => d.probability.toFixed(2));
        
        // Draw nodes
        this.nodeElements = this.g.selectAll('.node-circle')
            .data(this.nodes)
            .enter()
            .append('circle')
            .attr('class', d => `node-circle node-${d.type}`)
            .attr('r', 25)
            .call(this.getDragBehavior());
        
        // Add node labels (names)
        this.nodeLabels = this.g.selectAll('.node-label')
            .data(this.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-label')
            .text(d => d.name)
            .call(this.getDragBehavior());
        
        // Add node values below nodes
        this.nodeValues = this.g.selectAll('.node-value')
            .data(this.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-value')
            .attr('dy', 35)
            .text(d => `${d.value.toFixed(2)}`)
            .call(this.getDragBehavior());
        
        // Add tooltips
        this.addTooltips();
        
        // Start simulation
        this.simulation.on('tick', () => this.tick());
    }
    
    getDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    addTooltips() {
        // Create tooltip div
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background-color', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', 1000);
        
        // Add tooltip to nodes
        this.nodeElements
            .on('mouseover', (event, d) => {
                this.tooltip.transition()
                    .duration(200)
                    .style('opacity', 0.9);
                
                let tooltipText = `<strong>${d.name}</strong><br/>`;
                tooltipText += `Type: ${d.type}<br/>`;
                tooltipText += `Value: ${d.value.toFixed(3)}<br/>`;
                tooltipText += `Reward: ${d.reward.toFixed(3)}`;
                
                if (d.success_rate !== null) {
                    tooltipText += `<br/>Success Rate: ${(d.success_rate * 100).toFixed(1)}%`;
                }
                
                this.tooltip.html(tooltipText)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });
        
        // Add tooltip to links
        this.linkElements
            .on('mouseover', (event, d) => {
                this.tooltip.transition()
                    .duration(200)
                    .style('opacity', 0.9);
                
                let tooltipText = `<strong>${d.source.id} → ${d.target.id}</strong><br/>`;
                tooltipText += `Probability: ${(d.probability * 100).toFixed(1)}%`;
                
                if (d.is_policy) {
                    tooltipText += `<br/><em>Optimal Policy</em>`;
                }
                
                this.tooltip.html(tooltipText)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });
    }
    
    tick() {
        // Update link positions
        this.linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        // Update link label positions
        this.linkLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
        
        // Update node positions
        this.nodeElements
            .attr('cx', d => d.x = Math.max(25, Math.min(this.width - 25, d.x)))
            .attr('cy', d => d.y = Math.max(25, Math.min(this.height - 25, d.y)));
        
        // Update node label positions
        this.nodeLabels
            .attr('x', d => d.x)
            .attr('y', d => d.y + 5);
        
        // Update node value positions
        this.nodeValues
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
    
    relayout() {
        if (this.simulation) {
            // Reset node positions
            this.nodes.forEach(node => {
                node.x = Math.random() * this.width;
                node.y = Math.random() * this.height;
                node.fx = null;
                node.fy = null;
            });
            
            // Restart simulation
            this.simulation.alpha(1).restart();
        }
    }
    
    resetZoom() {
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);
    }
    
    clear() {
        this.g.selectAll('*').remove();
        if (this.simulation) {
            this.simulation.stop();
        }
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
    }
}
