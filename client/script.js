document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results-container');
    const claudeContent = document.getElementById('claude-content');
    const traceContent = document.getElementById('trace-content');
    const graphContainer = document.getElementById('graph-container');
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Submit button click handler
    submitBtn.addEventListener('click', function() {
        const query = queryInput.value.trim();
        
        if (!query) {
            alert('Please enter a research query.');
            return;
        }
        
        // Show loading, hide results
        loading.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        
        // Process query with Claude and ASR-GoT
        processQuery(query);
    });
    
    // Query processing function
    async function processQuery(query) {
        try {
            // Call the API
            const response = await fetch('/api/v1/claude/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    process_response: true
                })
            });
            
            if (!response.ok) {
                throw new Error('API request failed');
            }
            
            const data = await response.json();
            
            // Process and display results
            displayResults(data);
            
        } catch (error) {
            console.error('Error processing query:', error);
            loading.classList.add('hidden');
            alert('Error processing your query. Please try again.');
        }
    }
    
    // Display results function
    function displayResults(data) {
        // Hide loading, show results
        loading.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        
        // Display Claude's response
        const claudeResponse = data.choices && data.choices[0] && data.choices[0].message ? 
            data.choices[0].message.content : 'No response from Claude.';
        
        claudeContent.innerHTML = formatMarkdown(claudeResponse);
        
        // Display reasoning trace if available
        if (data.asr_got_result && data.asr_got_result.reasoning_trace) {
            let traceHtml = '<h3>ASR-GoT Reasoning Trace</h3>';
            
            data.asr_got_result.reasoning_trace.forEach((stage, index) => {
                traceHtml += `
                    <div class="trace-stage">
                        <h4>Stage ${stage.stage}: ${stage.name}</h4>
                        <p>${stage.summary}</p>
                        <div class="metrics">
                            <strong>Metrics:</strong>
                            <ul>
                                ${Object.entries(stage.metrics).map(([key, value]) => 
                                    `<li>${key}: ${typeof value === 'number' ? value.toFixed(2) : value}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            });
            
            // Add confidence information
            if (data.asr_got_result.confidence) {
                const conf = data.asr_got_result.confidence;
                traceHtml += `
                    <div class="confidence-section">
                        <h4>Final Confidence Assessment</h4>
                        <div class="confidence-dimension">
                            <strong>Empirical Support:</strong> ${conf[0].toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${conf[0] * 100}%;"></div>
                            </div>
                        </div>
                        <div class="confidence-dimension">
                            <strong>Theoretical Basis:</strong> ${conf[1].toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${conf[1] * 100}%;"></div>
                            </div>
                        </div>
                        <div class="confidence-dimension">
                            <strong>Methodological Rigor:</strong> ${conf[2].toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${conf[2] * 100}%;"></div>
                            </div>
                        </div>
                        <div class="confidence-dimension">
                            <strong>Consensus Alignment:</strong> ${conf[3].toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${conf[3] * 100}%;"></div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            traceContent.innerHTML = traceHtml;
        } else {
            traceContent.innerHTML = '<p>No reasoning trace available.</p>';
        }
        
        // Render graph visualization if graph data is available
        if (data.asr_got_result && data.asr_got_result.graph_state) {
            renderGraph(data.asr_got_result.graph_state);
        } else {
            graphContainer.innerHTML = '<p>No graph data available for visualization.</p>';
        }
    }
    
    // Simple markdown formatting function
    function formatMarkdown(text) {
        // Convert headers
        text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        
        // Convert bold and italic
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
       // Convert code blocks
       text = text.replace(/```([^`]*?)```/gs, '<pre><code>$1</code></pre>');
       text = text.replace(/`([^`]*?)`/g, '<code>$1</code>');
       
       // Convert lists
       text = text.replace(/^\* (.*$)/gm, '<ul><li>$1</li></ul>');
       text = text.replace(/^\d+\. (.*$)/gm, '<ol><li>$1</li></ol>');
       
       // Fix consecutive list items
       text = text.replace(/<\/ul>\s*<ul>/g, '');
       text = text.replace(/<\/ol>\s*<ol>/g, '');
       
       // Convert paragraphs
       text = text.replace(/\n\s*\n/g, '</p><p>');
       text = '<p>' + text + '</p>';
       
       return text;
   }
   
   // Graph visualization function using D3.js
   function renderGraph(graphState) {
       // Clear previous visualization
       graphContainer.innerHTML = '';
       
       // Extract nodes and edges from graph state
       const nodes = graphState.nodes.map(node => ({
           id: node.node_id,
           label: node.label,
           type: node.type,
           confidence: node.confidence
       }));
       
       const edges = graphState.edges.map(edge => ({
           id: edge.edge_id,
           source: edge.source,
           target: edge.target,
           type: edge.edge_type
       }));
       
       // Create D3 force simulation
       const width = graphContainer.clientWidth;
       const height = 600;
       
       // Set up SVG
       const svg = d3.select('#graph-container')
           .append('svg')
           .attr('width', width)
           .attr('height', height);
       
       // Define node colors by type
       const nodeColors = {
           'root': '#e74c3c',
           'dimension': '#3498db',
           'hypothesis': '#2ecc71',
           'evidence': '#f39c12',
           'interdisciplinary_bridge': '#9b59b6',
           'placeholder_gap': '#95a5a6'
       };
       
       // Define edge colors by type
       const edgeColors = {
           'supportive': '#2ecc71',
           'contradictory': '#e74c3c',
           'correlative': '#f39c12',
           'causal': '#9b59b6',
           'temporal': '#3498db',
           'decomposition': '#95a5a6',
           'hypothesis': '#34495e'
       };
       
       // Create arrow marker for directed edges
       svg.append('defs').append('marker')
           .attr('id', 'arrowhead')
           .attr('viewBox', '-0 -5 10 10')
           .attr('refX', 20)
           .attr('refY', 0)
           .attr('orient', 'auto')
           .attr('markerWidth', 6)
           .attr('markerHeight', 6)
           .attr('xoverflow', 'visible')
           .append('svg:path')
           .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
           .attr('fill', '#999')
           .style('stroke', 'none');
       
       // Create force simulation
       const simulation = d3.forceSimulation(nodes)
           .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
           .force('charge', d3.forceManyBody().strength(-300))
           .force('center', d3.forceCenter(width / 2, height / 2))
           .force('collide', d3.forceCollide().radius(60));
       
       // Draw edges
       const link = svg.append('g')
           .selectAll('line')
           .data(edges)
           .enter().append('line')
           .attr('stroke', d => edgeColors[d.type] || '#999')
           .attr('stroke-width', 1.5)
           .attr('marker-end', 'url(#arrowhead)');
       
       // Create node groups
       const node = svg.append('g')
           .selectAll('.node')
           .data(nodes)
           .enter().append('g')
           .attr('class', 'node')
           .call(d3.drag()
               .on('start', dragstarted)
               .on('drag', dragged)
               .on('end', dragended));
       
       // Add circles to nodes
       node.append('circle')
           .attr('r', d => {
               // Size based on confidence
               if (d.confidence && d.confidence.length > 0) {
                   const avgConfidence = d.confidence.reduce((a, b) => a + b, 0) / d.confidence.length;
                   return 5 + 15 * avgConfidence;
               }
               return 10; // Default size
           })
           .attr('fill', d => nodeColors[d.type] || '#999');
       
       // Add text labels to nodes
       node.append('text')
           .attr('dx', 12)
           .attr('dy', '.35em')
           .text(d => d.label);
       
       // Add titles for hover
       node.append('title')
           .text(d => `${d.label} (${d.id})\nType: ${d.type}\nConfidence: ${d.confidence ? d.confidence.map(c => c.toFixed(2)).join(', ') : 'N/A'}`);
       
       // Update positions during simulation
       simulation.on('tick', () => {
           link
               .attr('x1', d => d.source.x)
               .attr('y1', d => d.source.y)
               .attr('x2', d => d.target.x)
               .attr('y2', d => d.target.y);
           
           node
               .attr('transform', d => `translate(${d.x},${d.y})`);
       });
       
       // Drag functions
       function dragstarted(event, d) {
           if (!event.active) simulation.alphaTarget(0.3).restart();
           d.fx = d.x;
           d.fy = d.y;
       }
       
       function dragged(event, d) {
           d.fx = event.x;
           d.fy = event.y;
       }
       
       function dragended(event, d) {
           if (!event.active) simulation.alphaTarget(0);
           d.fx = null;
           d.fy = null;
       }
   }
});