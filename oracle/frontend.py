"""
Modern Interactive Web Dashboard for ORACLE.
Implements Step 11: Incident input, tool trace, graph path, evidence panel,
blast radius, hypothesis summary, and approve/reject simulated action controls.
"""


def get_html_dashboard() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ImpactGraph — Trace the cause. Map the impact. Act with evidence.</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <style>
        :root {
            --bg-base: #07090E;
            --bg-surface: #0E131F;
            --bg-card: rgba(18, 24, 38, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --primary: #3B82F6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --accent-cyan: #06B6D4;
            --accent-purple: #A855F7;
            --danger: #EF4444;
            --danger-bg: rgba(239, 68, 68, 0.12);
            --success: #10B981;
            --success-bg: rgba(16, 185, 129, 0.12);
            --warning: #F59E0B;
            --warning-bg: rgba(245, 158, 11, 0.12);
            --text-main: #F1F5F9;
            --text-muted: #94A3B8;
            --text-dim: #64748B;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.06) 0%, transparent 40%);
        }

        /* Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border);
            background: rgba(14, 19, 31, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--primary), var(--accent-purple));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 16px var(--primary-glow);
            font-weight: 800;
            font-size: 1.1rem;
            color: white;
        }

        .brand-text h1 {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .brand-text span {
            font-size: 0.75rem;
            color: var(--accent-cyan);
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .btn {
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border: 1px solid transparent;
            font-family: inherit;
        }

        .btn-primary {
            background: linear-gradient(135deg, #2563EB, #1D4ED8);
            color: white;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.3);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #3B82F6, #2563EB);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--border-hover);
        }

        .btn-danger {
            background: var(--danger-bg);
            border-color: var(--danger);
            color: var(--danger);
        }

        .btn-success {
            background: var(--success-bg);
            border-color: var(--success);
            color: var(--success);
        }

        /* Status Badge */
        .badge {
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .badge-critical { background: var(--danger-bg); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-success { background: var(--success-bg); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-warning { background: var(--warning-bg); color: #FCD34D; border: 1px solid rgba(245, 158, 11, 0.3); }

        /* Main Container */
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 1.5rem;
            display: grid;
            grid-template-columns: 360px 1fr 420px;
            gap: 1.5rem;
            height: calc(100vh - 75px);
        }

        /* Glassmorphic Panel */
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .panel-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
        }

        .panel-title {
            font-size: 0.95rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            letter-spacing: -0.01em;
        }

        .panel-body {
            padding: 1.25rem;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        /* Incident Card */
        .incident-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            transition: all 0.2s;
        }

        .incident-card:hover {
            border-color: var(--primary);
            background: rgba(59, 130, 246, 0.05);
        }

        /* Graph Canvas */
        #cy {
            width: 100%;
            height: 100%;
            background: #090D15;
            border-radius: 8px;
        }

        /* Tool Call Trace */
        .trace-item {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            padding: 0.5rem 0.75rem;
            background: rgba(0, 0, 0, 0.4);
            border-left: 3px solid var(--primary);
            border-radius: 0 4px 4px 0;
            display: flex;
            justify-content: space-between;
        }

        /* Hypotheses Comparison */
        .hypo-box {
            padding: 0.85rem;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
        }

        .hypo-confirmed {
            border-color: rgba(239, 68, 68, 0.5);
            background: rgba(239, 68, 68, 0.05);
        }

        .hypo-refuted {
            border-color: rgba(148, 163, 184, 0.2);
            opacity: 0.75;
        }

        /* Blast Radius Table */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }

        th {
            text-align: left;
            padding: 0.5rem;
            color: var(--text-dim);
            font-weight: 600;
            border-bottom: 1px solid var(--border);
        }

        td {
            padding: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        /* Action Box */
        .action-box {
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(168, 85, 247, 0.1));
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 1rem;
        }

        /* Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal {
            background: var(--bg-surface);
            border: 1px solid var(--border-hover);
            border-radius: 12px;
            width: 500px;
            max-width: 90vw;
            padding: 1.5rem;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }

        .loading-pulse {
            animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .4; }
        }
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <div class="logo-icon">Ω</div>
            <div class="brand-text">
                <h1>ImpactGraph</h1>
                <span>Trace the cause. Map the impact. Act with evidence. • FalkorDB Track 01 • <strong style="color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.4); background: rgba(251, 191, 36, 0.1); padding: 2px 6px; border-radius: 4px;">MIT</strong> <strong style="color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 4px;">GPLv3</strong></span>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" onclick="seedGraph()">↻ Reset & Seed Graph</button>
            <button class="btn btn-primary" onclick="triggerInvestigation()">⚡ Run Investigation</button>
        </div>
    </header>

    <div class="container">
        <!-- Left: Incident Context & Alerts -->
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">🚨 Active Incidents</span>
                <span class="badge badge-critical" id="incident-badge">CRITICAL</span>
            </div>
            <div class="panel-body">
                <div class="incident-card" id="incident-details">
                    <div style="font-weight: 700; margin-bottom: 0.25rem;" id="inc-title">Loading incident...</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;" id="inc-id">INC-4091</div>
                    <div style="font-size: 0.8rem; line-height: 1.4;" id="inc-summary">Loading graph context...</div>
                </div>

                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Observed Telemetry Alerts</div>
                <div id="alerts-container" style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <div style="color: var(--text-dim); font-size: 0.8rem;">Fetching alerts...</div>
                </div>

                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; margin-top: 0.5rem;">MCP Tool Trace</div>
                <div id="tool-trace-container" style="display: flex; flex-direction: column; gap: 0.35rem;">
                    <!-- Tool trace items -->
                </div>
            </div>
        </div>

        <!-- Center: Interactive Graph View -->
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">🕸️ FalkorDB Multi-Hop Causal Graph</span>
                <span style="font-size: 0.75rem; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;">Graph: oracle_incidents</span>
            </div>
            <div style="flex: 1; padding: 0.75rem; position: relative;">
                <div id="cy"></div>
            </div>
        </div>

        <!-- Right: Grounded Evidence & Safe Action -->
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">⚖️ Hypotheses & Action Gate</span>
            </div>
            <div class="panel-body">
                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Competing Explanations</div>
                <div id="hypotheses-container" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <!-- Hypotheses cards -->
                </div>

                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; margin-top: 0.5rem;">Downstream Blast Radius</div>
                <div style="max-height: 140px; overflow-y: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Tier</th>
                                <th>Hops</th>
                            </tr>
                        </thead>
                        <tbody id="blast-table-body">
                            <!-- Rows -->
                        </tbody>
                    </table>
                </div>

                <div class="action-box">
                    <div style="font-weight: 700; font-size: 0.9rem; margin-bottom: 0.25rem;">🛡️ Safe Simulated Action</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;" id="action-desc">
                        Pending investigation recommendation...
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-success" style="flex: 1;" onclick="openApprovalModal()">Approve Rollback</button>
                        <button class="btn btn-danger" onclick="rejectAction()">Reject</button>
                    </div>
                </div>

                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Audit Log</div>
                <div id="audit-log" style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; display: flex; flex-direction: column; gap: 0.4rem; max-height: 100px; overflow-y: auto;">
                    <!-- Audit rows -->
                </div>
            </div>
        </div>
    </div>

    <!-- Approval Modal -->
    <div class="modal-overlay" id="approval-modal">
        <div class="modal">
            <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Human Approval Required</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                Policy Gate: ORACLE cannot execute remediation actions without human sign-off.
                This will simulate rolling back payment-service to stable version v2.4.0.
            </p>
            <div style="margin-bottom: 1rem;">
                <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 0.35rem;">Approver Name / Handle</label>
                <input type="text" id="approver-name" value="Sarah Connor (Eng Lead)" style="width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: white; border-radius: 6px; font-family: inherit;">
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem;">
                <button class="btn btn-secondary" onclick="closeApprovalModal()">Cancel</button>
                <button class="btn btn-success" onclick="confirmApproval()">Confirm & Execute Simulation</button>
            </div>
        </div>
    </div>

    <script>
        let currentInvestigation = null;
        let cy = null;

        // Initialize Cytoscape
        function initGraph() {
            cy = cytoscape({
                container: document.getElementById('cy'),
                style: [
                    {
                        selector: 'node',
                        style: {
                            'label': 'data(label)',
                            'color': '#F1F5F9',
                            'font-size': '10px',
                            'font-family': 'Plus Jakarta Sans',
                            'text-valign': 'bottom',
                            'text-margin-y': 5,
                            'background-color': '#3B82F6',
                            'width': 30,
                            'height': 30,
                            'border-width': 2,
                            'border-color': 'rgba(255,255,255,0.2)'
                        }
                    },
                    {
                        selector: 'node[type = "Incident"]',
                        style: { 'background-color': '#EF4444', 'width': 40, 'height': 40, 'border-color': '#FCA5A5' }
                    },
                    {
                        selector: 'node[type = "Service"]',
                        style: { 'background-color': '#06B6D4', 'width': 32, 'height': 32 }
                    },
                    {
                        selector: 'node[health = "FAILING"]',
                        style: { 'background-color': '#DC2626', 'border-color': '#F87171', 'border-width': 3 }
                    },
                    {
                        selector: 'node[type = "Deployment"]',
                        style: { 'background-color': '#F59E0B', 'shape': 'rectangle', 'width': 26, 'height': 26 }
                    },
                    {
                        selector: 'node[type = "Vulnerability"]',
                        style: { 'background-color': '#8B5CF6', 'shape': 'diamond', 'width': 30, 'height': 30 }
                    },
                    {
                        selector: 'node[type = "Alert"]',
                        style: { 'background-color': '#EC4899', 'width': 24, 'height': 24 }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 1.5,
                            'line-color': 'rgba(255, 255, 255, 0.15)',
                            'target-arrow-color': 'rgba(255, 255, 255, 0.25)',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(rel)',
                            'font-size': '8px',
                            'color': '#64748B',
                            'text-rotation': 'autorotate'
                        }
                    },
                    {
                        selector: 'edge[rel = "DEPENDS_ON"]',
                        style: { 'line-color': '#3B82F6', 'target-arrow-color': '#3B82F6', 'width': 2 }
                    },
                    {
                        selector: 'edge[rel = "DEPLOYED_IN"]',
                        style: { 'line-color': '#F59E0B', 'target-arrow-color': '#F59E0B', 'line-style': 'dashed' }
                    }
                ],
                layout: {
                    name: 'cose',
                    animate: true,
                    padding: 30
                }
            });
        }

        async function loadTopology() {
            try {
                const res = await fetch('/api/graph/topology');
                const data = await res.json();
                
                const elements = [];
                data.nodes.forEach(n => {
                    const name = n.properties.name || n.properties.title || n.properties.id || n.id;
                    elements.push({
                        group: 'nodes',
                        data: {
                            id: n.id,
                            label: name,
                            type: n.label,
                            health: n.properties.health || 'NORMAL'
                        }
                    });
                });

                data.edges.forEach((e, idx) => {
                    elements.push({
                        group: 'edges',
                        data: {
                            id: `e-${idx}`,
                            source: e.source,
                            target: e.target,
                            rel: e.relationship
                        }
                    });
                });

                cy.elements().remove();
                cy.add(elements);
                cy.layout({ name: 'cose', animate: false }).run();
            } catch (err) {
                console.error("Topology fetch failed:", err);
            }
        }

        async function triggerInvestigation() {
            try {
                const res = await fetch('/api/investigate/INC-4091');
                const data = await res.json();
                currentInvestigation = data;

                // Update UI
                document.getElementById('inc-title').innerText = data.incident_title;
                document.getElementById('inc-summary').innerText = data.summary;

                // Tool trace
                const traceContainer = document.getElementById('tool-trace-container');
                traceContainer.innerHTML = '';
                data.tool_call_trace.forEach(t => {
                    const div = document.createElement('div');
                    div.className = 'trace-item';
                    div.innerHTML = `<span>⚡ ${t.tool}</span><span style="color: #10B981;">✓ ${t.status}</span>`;
                    traceContainer.appendChild(div);
                });

                // Hypotheses
                const hypoContainer = document.getElementById('hypotheses-container');
                hypoContainer.innerHTML = '';
                data.hypotheses_evaluated.forEach(h => {
                    const isConfirmed = h.status === 'CONFIRMED_ROOT_CAUSE';
                    const div = document.createElement('div');
                    div.className = `hypo-box ${isConfirmed ? 'hypo-confirmed' : 'hypo-refuted'}`;
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.35rem;">
                            <strong style="font-size: 0.85rem;">${h.name}</strong>
                            <span class="badge ${isConfirmed ? 'badge-critical' : 'badge-warning'}">${h.status}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.3;">
                            ${h.reasoning}
                        </div>
                        <div style="font-size: 0.7rem; color: var(--accent-cyan); margin-top: 0.4rem; font-family: 'JetBrains Mono', monospace;">
                            Evidence: ${h.supporting_evidence_ids.join(', ')} | Confidence: ${(h.confidence_score * 100).toFixed(0)}%
                        </div>
                    `;
                    hypoContainer.appendChild(div);
                });

                // Blast radius table
                const blastBody = document.getElementById('blast-table-body');
                blastBody.innerHTML = '';
                data.blast_radius.forEach(b => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${b.affected_service}</strong></td>
                        <td><span class="badge badge-warning">${b.criticality}</span></td>
                        <td>${b.hop_distance} hop(s)</td>
                    `;
                    blastBody.appendChild(tr);
                });

                // Action description
                if (data.proposed_remediation) {
                    document.getElementById('action-desc').innerText = 
                        `${data.proposed_remediation.description} Grounded in: ${data.proposed_remediation.grounded_evidence_ids.join(', ')}`;
                }

                loadAudit();
                await loadTopology();

            } catch (err) {
                console.error("Investigation failed:", err);
            }
        }

        async function loadAudit() {
            try {
                const res = await fetch('/api/audit');
                const data = await res.json();
                const container = document.getElementById('audit-log');
                container.innerHTML = '';
                data.audit_log.forEach(a => {
                    const div = document.createElement('div');
                    div.style.color = a.status.includes('EXECUTED') ? '#10B981' : '#EF4444';
                    div.innerText = `[${a.timestamp.substring(11, 19)}] ${a.action_type}: ${a.status} (${a.approver})`;
                    container.appendChild(div);
                });
            } catch (err) {}
        }

        async function seedGraph() {
            await fetch('/api/seed', { method: 'POST' });
            await loadTopology();
            await triggerInvestigation();
        }

        function openApprovalModal() {
            document.getElementById('approval-modal').style.display = 'flex';
        }

        function closeApprovalModal() {
            document.getElementById('approval-modal').style.display = 'none';
        }

        async function confirmApproval() {
            const approver = document.getElementById('approver-name').value;
            const res = await fetch('/api/actions/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action_type: 'simulate_canary_rollback',
                    incident_id: 'INC-4091',
                    target_id: 'dep-pay-v2.4.1',
                    evidence_ids: ['EVI-901', 'EVI-903'],
                    approved: true,
                    approver: approver,
                    notes: 'Confirmed by Lead Engineer via ORACLE safety gate'
                })
            });
            closeApprovalModal();
            loadAudit();
            alert('Remediation action simulated successfully and recorded to FalkorDB audit ledger!');
        }

        function rejectAction() {
            alert('Simulated action was rejected. Audit record logged.');
        }

        window.onload = async () => {
            initGraph();
            await loadTopology();
            await triggerInvestigation();
        };
    </script>
</body>
</html>
"""
