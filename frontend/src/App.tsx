import React, { useState, useEffect } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import { FindingsPanel } from './components/FindingsPanel';
import { HypothesesSection } from './components/HypothesesSection';
import { ActionModal } from './components/ActionModal';
import type {
  Incident,
  InvestigationReport,
  GraphTopology,
  AuditRecord,
} from './types';

export const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('INC-4091');
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [topology, setTopology] = useState<GraphTopology | null>(null);
  const [auditLog, setAuditLog] = useState<AuditRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [systemHealth, setSystemHealth] = useState<{ connected: boolean; host: string }>({
    connected: false,
    host: 'localhost:6379',
  });

  // Load initial system data
  useEffect(() => {
    fetchHealth();
    fetchIncidents();
    fetchTopology();
    fetchAudit();
  }, []);

  // When incident selection changes, trigger investigation
  useEffect(() => {
    if (selectedIncidentId) {
      runInvestigation(selectedIncidentId);
    }
  }, [selectedIncidentId]);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/health');
      const data = await res.json();
      setSystemHealth({
        connected: data.falkordb_connected,
        host: `${data.falkordb_host}:${data.falkordb_port}`,
      });
    } catch {
      setSystemHealth({ connected: false, host: 'localhost:6379' });
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch('/incidents');
      const data = await res.json();
      setIncidents(data.incidents || []);
    } catch (err) {
      console.error('Failed to fetch incidents', err);
    }
  };

  const fetchTopology = async () => {
    try {
      const res = await fetch('/api/graph/topology');
      const data = await res.json();
      setTopology(data);
    } catch (err) {
      console.error('Failed to fetch graph topology', err);
    }
  };

  const fetchAudit = async () => {
    try {
      const res = await fetch('/audit');
      const data = await res.json();
      setAuditLog(data.audit_log || []);
    } catch (err) {
      console.error('Failed to fetch audit log', err);
    }
  };

  const runInvestigation = async (incidentId: string) => {
    try {
      setIsLoading(true);
      const res = await fetch(`/incidents/${incidentId}/investigate`, { method: 'POST' });
      const data = await res.json();
      setReport(data);
      setIsLoading(false);
      fetchTopology();
      fetchAudit();
    } catch (err) {
      console.error('Investigation failed', err);
      setIsLoading(false);
    }
  };

  const handleSeed = async () => {
    try {
      setIsLoading(true);
      await fetch('/seed', { method: 'POST' });
      await fetchIncidents();
      await fetchTopology();
      if (selectedIncidentId) {
        await runInvestigation(selectedIncidentId);
      }
      setIsLoading(false);
    } catch (err) {
      console.error('Seeding failed', err);
      setIsLoading(false);
    }
  };

  const handleApproveAction = async (actionId: string, approver: string, notes: string) => {
    const res = await fetch(`/actions/${actionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approver, notes }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Approval failed');
    }

    await fetchAudit();
    if (selectedIncidentId) {
      await runInvestigation(selectedIncidentId);
    }
  };

  const currentIncident = incidents.find((i) => i.id === selectedIncidentId);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.85rem 1.75rem',
          borderBottom: '1px solid var(--border)',
          background: 'rgba(14, 19, 31, 0.85)',
          backdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              background: 'linear-gradient(135deg, #3B82F6, #A855F7)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.1rem',
              color: 'white',
              boxShadow: '0 0 16px rgba(59, 130, 246, 0.3)',
            }}
          >
            Ω
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.1rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#F1F5F9' }}>
                ImpactGraph
              </h1>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  background: 'rgba(245, 158, 11, 0.15)',
                  color: '#FCD34D',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                }}
              >
                SYNTHETIC TEST ENVIRONMENT
              </span>
            </div>
            <span style={{ fontSize: '0.72rem', color: '#06B6D4', fontWeight: 600 }}>
              Trace the cause. Map the impact. Act with evidence. • Track 01
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: '#94A3B8',
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '4px 10px',
              borderRadius: '999px',
              border: '1px solid var(--border)',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: systemHealth.connected ? '#10B981' : '#EF4444',
                boxShadow: systemHealth.connected ? '0 0 8px #10B981' : 'none',
              }}
            />
            <span>FalkorDB: {systemHealth.host}</span>
          </div>

          <button className="btn btn-secondary" onClick={handleSeed} disabled={isLoading}>
            ↻ Reset & Seed Graph
          </button>
          <button
            className="btn btn-primary"
            onClick={() => runInvestigation(selectedIncidentId)}
            disabled={isLoading}
          >
            {isLoading ? 'Investigating...' : '⚡ Re-Investigate'}
          </button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <main
        style={{
          flex: 1,
          padding: '1.25rem',
          display: 'grid',
          gridTemplateColumns: '360px 1fr 420px',
          gap: '1.25rem',
          maxWidth: '1800px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        {/* Left Column: Context, Incidents & Alerts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Incident Selector */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">🚨 Active Incidents</span>
              <span className="badge badge-critical">{currentIncident?.severity || 'CRITICAL'}</span>
            </div>
            <div className="panel-body">
              <div style={{ marginBottom: '0.5rem' }}>
                <label style={{ fontSize: '0.75rem', color: '#64748B', display: 'block', marginBottom: '4px' }}>
                  Select Target Incident
                </label>
                <select
                  value={selectedIncidentId}
                  onChange={(e) => setSelectedIncidentId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    color: 'white',
                    fontFamily: 'inherit',
                    fontSize: '0.82rem',
                  }}
                >
                  {incidents.map((inc) => (
                    <option key={inc.id} value={inc.id}>
                      {inc.id} — {inc.title}
                    </option>
                  ))}
                </select>
              </div>

              {currentIncident && (
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#F1F5F9', marginBottom: '4px' }}>
                    {currentIncident.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8', lineHeight: 1.35 }}>
                    {currentIncident.description}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: '6px' }}>
                    Triggered: {currentIncident.created_at}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* MCP Tool Execution Trace */}
          <div className="panel" style={{ flex: 1 }}>
            <div className="panel-header">
              <span className="panel-title">⚡ MCP Tool Execution Trace</span>
              <span style={{ fontSize: '0.7rem', color: '#06B6D4', fontFamily: 'monospace' }}>
                {report?.tool_call_trace.length || 0} tools executed
              </span>
            </div>
            <div className="panel-body" style={{ gap: '0.4rem' }}>
              {report?.tool_call_trace.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '0.75rem',
                    padding: '6px 10px',
                    background: 'rgba(0, 0, 0, 0.35)',
                    borderLeft: '3px solid #3B82F6',
                    borderRadius: '0 4px 4px 0',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ color: '#E2E8F0' }}>{step.tool}</span>
                  <span style={{ color: '#10B981', fontWeight: 600 }}>✓ {step.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Column: Interactive Graph & Findings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Cytoscape Graph Canvas */}
          <div className="panel" style={{ height: '420px' }}>
            <div className="panel-header">
              <span className="panel-title">🕸️ FalkorDB Multi-Hop Causal Graph</span>
              <span style={{ fontSize: '0.75rem', color: '#06B6D4', fontFamily: 'monospace' }}>
                Graph: oracle_incidents
              </span>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              <GraphCanvas topology={topology} highlightedPath={report?.graph_path} />
            </div>
          </div>

          {/* Categorized Findings */}
          <div className="panel" style={{ flex: 1 }}>
            <div className="panel-header">
              <span className="panel-title">📋 Grounded Findings Breakdown</span>
              <span style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
                OBSERVED • INFERRED • UNKNOWN
              </span>
            </div>
            <div className="panel-body">
              {report?.findings ? (
                <FindingsPanel findings={report.findings} />
              ) : (
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Awaiting investigation findings...</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Hypotheses, Blast Radius, Actions & Audit */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Competing Hypotheses */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">⚖️ Competing Hypotheses</span>
            </div>
            <div className="panel-body">
              {report?.hypotheses_evaluated ? (
                <HypothesesSection hypotheses={report.hypotheses_evaluated} />
              ) : (
                <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Comparing candidate causes...</div>
              )}
            </div>
          </div>

          {/* Downstream Blast Radius */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">💥 Downstream Blast Radius</span>
              <span style={{ fontSize: '0.72rem', color: '#EF4444' }}>
                {report?.blast_radius.length || 0} services impacted
              </span>
            </div>
            <div className="panel-body" style={{ padding: '0.5rem 1rem' }}>
              <table>
                <thead>
                  <tr>
                    <th>Service</th>
                    <th>Tier</th>
                    <th>Distance</th>
                  </tr>
                </thead>
                <tbody>
                  {report?.blast_radius.map((b, idx) => (
                    <tr key={idx}>
                      <td>
                        <strong style={{ color: '#E2E8F0' }}>{b.affected_service}</strong>
                      </td>
                      <td>
                        <span className="badge badge-warning">{b.criticality}</span>
                      </td>
                      <td style={{ color: '#94A3B8' }}>{b.hop_distance} hop(s)</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Safe Action Proposal & Human Approval Gate */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(168, 85, 247, 0.1))',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '12px',
              padding: '1.1rem',
            }}
          >
            <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#F1F5F9', marginBottom: '0.35rem' }}>
              🛡️ Safe Simulated Action Gate
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94A3B8', marginBottom: '0.75rem', lineHeight: 1.35 }}>
              {report?.proposed_remediation?.description || 'Awaiting investigation proposal...'}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className="btn btn-success"
                style={{ flex: 1 }}
                onClick={() => setIsModalOpen(true)}
                disabled={!report?.proposed_remediation}
              >
                Approve Simulated Action
              </button>
            </div>
          </div>

          {/* Audit Ledger */}
          <div className="panel" style={{ flex: 1 }}>
            <div className="panel-header">
              <span className="panel-title">📜 Audit Trail</span>
              <span style={{ fontSize: '0.72rem', color: '#10B981' }}>{auditLog.length} events</span>
            </div>
            <div className="panel-body" style={{ gap: '0.4rem', maxHeight: '160px' }}>
              {auditLog.map((log) => (
                <div
                  key={log.audit_id}
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '0.7rem',
                    color: log.status.includes('EXECUTED') ? '#6EE7B7' : '#FCA5A5',
                    background: 'rgba(0, 0, 0, 0.3)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                  }}
                >
                  [{log.timestamp.substring(11, 19)}] {log.action_type}: {log.status} ({log.actor})
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Human Approval Modal */}
      <ActionModal
        proposal={report?.proposed_remediation || null}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onApprove={handleApproveAction}
      />
    </div>
  );
};

export default App;
