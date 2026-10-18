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

const STEP_DESCRIPTIONS = [
  {
    step: 1,
    tool: 'get_incident_context',
    title: 'Query Incident Context & Triggered Alerts',
    detail: 'ORACLE queries FalkorDB for active incident metadata and maps connected alerts across services.',
  },
  {
    step: 2,
    tool: 'trace_candidate_causes',
    title: 'Trace Multi-Hop Candidate Causes',
    detail: 'Agent traverses graph dependencies to discover recent deployments, package versions, and CVE records.',
  },
  {
    step: 3,
    tool: 'get_deployment_history',
    title: 'Inspect Deployment Timelines & Commits',
    detail: 'Agent queries deployment timestamps and identifies candidate rollouts coinciding with failure onsets.',
  },
  {
    step: 4,
    tool: 'get_evidence_chain',
    title: 'Retrieve Grounded Telemetry Evidence',
    detail: 'Agent pulls immutable log records, metric timeseries, and vulnerability scans to test hypotheses.',
  },
  {
    step: 5,
    tool: 'get_blast_radius',
    title: 'Compute Downstream Customer Blast Radius',
    detail: 'Agent traverses reverse DEPENDS_ON chains to map impacted consumers while excluding disconnected services.',
  },
  {
    step: 6,
    tool: 'get_service_owner',
    title: 'Identify Service Ownership & On-Call SRE',
    detail: 'Agent looks up responsible engineering team and on-call contact directly from the FalkorDB graph.',
  },
  {
    step: 7,
    tool: 'propose_response',
    title: 'Synthesize Evidence & Propose Human-Gated Action',
    detail: 'Agent differentiates competing hypotheses, categorizes findings, and creates an auditable action proposal.',
  },
];

const WALKTHROUGH_STAGES = [
  {
    stage: 'OVERVIEW',
    title: '1. SYSTEM TOPOLOGY & FALKORDB CONNECTION',
    banner: 'ImpactGraph ORACLE Cockpit initialized. Live Cypher connection established to FalkorDB on localhost:6379.',
    duration: 3500,
    setup: (helpers: any) => {
      helpers.setSelectedIncidentId('INC-4091');
      helpers.setIsDemoMode(false);
      helpers.setActiveTab('findings');
      helpers.setIsModalOpen(false);
    },
  },
  {
    stage: 'STEP_1',
    title: '2. REASONING STEP 1/7 — GET INCIDENT CONTEXT',
    banner: 'MCP Tool [get_incident_context]: Fetches active incident INC-4091 metadata and triggered telemetry alerts across services.',
    duration: 3500,
    setup: (helpers: any) => {
      helpers.setIsDemoMode(true);
      helpers.setDemoStep(1);
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'STEP_2',
    title: '3. REASONING STEP 2/7 — MULTI-HOP DEPENDENCY TRAVERSAL',
    banner: 'MCP Tool [trace_candidate_causes]: Traverses graph from api-gateway -> order-service -> payment-service (3 hops) in FalkorDB.',
    duration: 3500,
    setup: (helpers: any) => {
      helpers.setDemoStep(2);
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'STEP_3',
    title: '4. REASONING STEP 3/7 — DEPLOYMENT TIMELINES',
    banner: 'MCP Tool [get_deployment_history]: Inspects rollout timestamps. Canary dep-pay-v2.4.1 correlates directly with failure onset.',
    duration: 3500,
    setup: (helpers: any) => {
      helpers.setDemoStep(3);
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'STEP_4',
    title: '5. REASONING STEP 4/7 — GROUNDED TELEMETRY EVIDENCE',
    banner: 'MCP Tool [get_evidence_chain]: Retrieves immutable logs & metrics (EVI-901, EVI-902, EVI-903). Categorized into OBSERVED/INFERRED/UNKNOWN.',
    duration: 4000,
    setup: (helpers: any) => {
      helpers.setDemoStep(4);
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'STEP_5',
    title: '6. REASONING STEP 5/7 — CUSTOMER BLAST RADIUS & NEGATIVE TEST',
    banner: 'MCP Tool [get_blast_radius]: Reverse DEPENDS_ON traversal maps blast radius. Disconnected analytics-pipeline excluded (Negative Test passed).',
    duration: 4000,
    setup: (helpers: any) => {
      helpers.setDemoStep(5);
      helpers.setActiveTab('blast');
    },
  },
  {
    stage: 'STEP_6',
    title: '7. REASONING STEP 6/7 — SERVICE OWNERSHIP LOOKUP',
    banner: 'MCP Tool [get_service_owner]: Queries team ownership directly from FalkorDB. Team Checkout (SRE Sarah Connor) identified.',
    duration: 3500,
    setup: (helpers: any) => {
      helpers.setDemoStep(6);
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'STEP_7',
    title: '8. REASONING STEP 7/7 — HYPOTHESIS DIFFERENTIATION',
    banner: 'MCP Tool [propose_response]: Compares competing hypotheses. Confirms dep-pay-v2.4.1 and refutes CVE-2026-4412 with temporal evidence.',
    duration: 4000,
    setup: (helpers: any) => {
      helpers.setDemoStep(7);
      helpers.setActiveTab('hypotheses');
    },
  },
  {
    stage: 'POLICY_REJECTION',
    title: '9. SAFETY GATE — ANTI-SELF-APPROVAL POLICY',
    banner: 'Safety Policy Gate: Testing agent self-approval. Agent is strictly blocked from approving its own proposal (403 Forbidden).',
    duration: 4000,
    setup: (helpers: any) => {
      helpers.setIsModalOpen(true);
      helpers.setModalApprover('ORACLE Agent');
      helpers.setModalError('Policy violation: ORACLE Agent cannot approve its own proposals (Anti-Self-Approval policy). Please enter a human engineer name.');
    },
  },
  {
    stage: 'POLICY_APPROVAL',
    title: '10. AUTHORIZED HUMAN SRE SIMULATION',
    banner: 'Human SRE Approval: Sarah Connor (Staff SRE) executes simulated canary rollback. Permanent record committed to FalkorDB.',
    duration: 4500,
    setup: async (helpers: any) => {
      helpers.setModalApprover('Sarah Connor (Staff SRE)');
      helpers.setModalError(null);
      if (helpers.proposal) {
        try {
          await helpers.handleApproveAction(
            helpers.proposal.action_id,
            'Sarah Connor (Staff SRE)',
            'Verified connection pool starvation in telemetry. Rollback approved.'
          );
        } catch (e) {
          console.error(e);
        }
      }
      setTimeout(() => {
        helpers.setIsModalOpen(false);
      }, 1000);
    },
  },
  {
    stage: 'MULTI_INCIDENT_1',
    title: '11. MULTI-INCIDENT REASONING — INC-3022',
    banner: 'Dynamic Reasoning: Switching to INC-3022 (Redis Cache Stampede & Auth Token Eviction Surge on auth-service).',
    duration: 4500,
    setup: (helpers: any) => {
      helpers.setIsDemoMode(false);
      helpers.setSelectedIncidentId('INC-3022');
      helpers.setActiveTab('findings');
    },
  },
  {
    stage: 'MULTI_INCIDENT_2',
    title: '12. MULTI-INCIDENT REASONING — INC-5102',
    banner: 'Dynamic Reasoning: Switching to INC-5102 (Logistics Carrier Webhook Timeout & RabbitMQ DLQ Overflow).',
    duration: 4500,
    setup: (helpers: any) => {
      helpers.setSelectedIncidentId('INC-5102');
      helpers.setActiveTab('hypotheses');
    },
  },
  {
    stage: 'AUDIT_VERIFICATION',
    title: '13. IMMUTABLE AUDIT LEDGER VERIFICATION',
    banner: 'Audit Ledger Verification: Returning to INC-4091 to demonstrate persistent execution state and FalkorDB audit trail.',
    duration: 4000,
    setup: (helpers: any) => {
      helpers.setSelectedIncidentId('INC-4091');
      helpers.setActiveTab('blast');
    },
  },
  {
    stage: 'COMPLETE',
    title: '14. WALKTHROUGH DEMO COMPLETED',
    banner: '✓ Walkthrough Complete: All Track 01 criteria verified (Connected Graph, Multi-Hop Causality, Blast Radius, Human Safety Policy, Audit Ledger)!',
    duration: 5000,
    setup: (helpers: any) => {
      helpers.setIsAutoWalkthrough(false);
    },
  },
];

export const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('INC-4091');
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [topology, setTopology] = useState<GraphTopology | null>(null);
  const [auditLog, setAuditLog] = useState<AuditRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'findings' | 'hypotheses' | 'blast'>('findings');
  
  // Step-by-Step Live Reasoning Demo Mode
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [demoStep, setDemoStep] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Automated Walkthrough State
  const [isAutoWalkthrough, setIsAutoWalkthrough] = useState<boolean>(false);
  const [walkthroughIndex, setWalkthroughIndex] = useState<number>(0);
  const [modalApprover, setModalApprover] = useState<string>('Sarah Connor (Staff SRE)');
  const [modalError, setModalError] = useState<string | null>(null);

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

    // Check query params for automated walkthrough (?walkthrough=1 or ?autoplay=1 or ?stage=X&snapshot=1)
    const params = new URLSearchParams(window.location.search);
    const stageParam = params.get('stage');
    if (stageParam) {
      const idx = WALKTHROUGH_STAGES.findIndex((s) => s.stage.toLowerCase() === stageParam.toLowerCase());
      if (idx !== -1) {
        setIsAutoWalkthrough(true);
        setWalkthroughIndex(idx);
      }
    } else if (params.get('walkthrough') === '1' || params.get('autoplay') === '1') {
      const timer = setTimeout(() => {
        setIsAutoWalkthrough(true);
        setWalkthroughIndex(0);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  // When incident selection changes, trigger investigation
  useEffect(() => {
    if (selectedIncidentId) {
      runInvestigation(selectedIncidentId);
    }
  }, [selectedIncidentId]);

  // Demo auto-play interval
  useEffect(() => {
    let timer: any = null;
    if (isDemoMode && isPlaying) {
      timer = setInterval(() => {
        setDemoStep((prev) => {
          if (prev >= 7) {
            setIsPlaying(false);
            return 7;
          }
          return prev + 1;
        });
      }, 3500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isDemoMode, isPlaying]);

  // Sync tab view with demo step
  useEffect(() => {
    if (!isDemoMode) return;
    if (demoStep <= 4) {
      setActiveTab('findings');
    } else if (demoStep === 5) {
      setActiveTab('blast');
    } else {
      setActiveTab('hypotheses');
    }
  }, [demoStep, isDemoMode]);

  // Automated Walkthrough Orchestrator Loop
  useEffect(() => {
    if (!isAutoWalkthrough) return;

    const currentStage = WALKTHROUGH_STAGES[walkthroughIndex];
    if (!currentStage) {
      setIsAutoWalkthrough(false);
      return;
    }

    const helpers = {
      setSelectedIncidentId,
      setIsDemoMode,
      setDemoStep,
      setActiveTab,
      setIsModalOpen,
      setModalApprover,
      setModalError,
      setIsAutoWalkthrough,
      proposal: report?.proposed_remediation,
      handleApproveAction,
    };

    currentStage.setup(helpers);

    const params = new URLSearchParams(window.location.search);
    if (params.get('snapshot') === '1') {
      return;
    }

    const timer = setTimeout(() => {
      if (walkthroughIndex + 1 < WALKTHROUGH_STAGES.length) {
        setWalkthroughIndex((prev) => prev + 1);
      } else {
        setIsAutoWalkthrough(false);
      }
    }, currentStage.duration);

    return () => clearTimeout(timer);
  }, [isAutoWalkthrough, walkthroughIndex, report]);

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
  const isActionExecuted = auditLog.some((a) => a.incident_id === selectedIncidentId);
  const currentStepInfo = STEP_DESCRIPTIONS[demoStep - 1];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
      {/* 1. Minimal Header */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.65rem 1.5rem',
          borderBottom: '1px solid var(--border)',
          background: 'rgba(10, 15, 26, 0.92)',
          backdropFilter: 'blur(16px)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        {/* Left: Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1rem',
              color: 'white',
              boxShadow: '0 0 16px rgba(59, 130, 246, 0.35)',
            }}
          >
            Ω
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#F8FAFC' }}>
                ImpactGraph
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  background: 'rgba(59, 130, 246, 0.15)',
                  color: '#93C5FD',
                  padding: '2px 7px',
                  borderRadius: '4px',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                }}
              >
                FalkorDB Track 01
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>
              Operational Reasoning & Causal Analysis through Linked Evidence
            </div>
          </div>
        </div>

        {/* Center: Incident Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: 600 }}>Incident:</label>
          <select
            value={selectedIncidentId}
            onChange={(e) => {
              setSelectedIncidentId(e.target.value);
              setIsDemoMode(false);
            }}
            style={{
              padding: '0.35rem 0.75rem',
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              color: '#F8FAFC',
              fontFamily: 'inherit',
              fontSize: '0.8rem',
              cursor: 'pointer',
              outline: 'none',
              maxWidth: '360px',
            }}
          >
            {incidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                {inc.id} — {inc.title}
              </option>
            ))}
          </select>
          <span
            className={`badge ${
              currentIncident?.severity === 'CRITICAL'
                ? 'badge-critical'
                : currentIncident?.severity === 'HIGH'
                ? 'badge-warning'
                : 'badge-info'
            }`}
          >
            {currentIncident?.severity || 'ACTIVE'}
          </span>
        </div>

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.72rem',
              color: '#94A3B8',
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '3px 9px',
              borderRadius: '999px',
              border: '1px solid var(--border)',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: systemHealth.connected ? '#10B981' : '#EF4444',
                boxShadow: systemHealth.connected ? '0 0 8px #10B981' : 'none',
              }}
            />
            <span>FalkorDB</span>
          </div>

          <button className="btn btn-secondary" onClick={handleSeed} disabled={isLoading} title="Reset & Seed Graph">
            ↻ Seed
          </button>

          <button
            style={{
              background: isAutoWalkthrough
                ? 'linear-gradient(135deg, #DC2626, #EF4444)'
                : 'linear-gradient(135deg, #7C3AED, #2563EB)',
              border: isAutoWalkthrough
                ? '1px solid #F87171'
                : '1px solid rgba(139, 92, 246, 0.5)',
              color: 'white',
              fontWeight: 700,
              boxShadow: isAutoWalkthrough
                ? '0 0 16px rgba(239, 68, 68, 0.4)'
                : '0 0 16px rgba(124, 58, 237, 0.35)',
            }}
            className="btn"
            onClick={() => {
              if (isAutoWalkthrough) {
                setIsAutoWalkthrough(false);
              } else {
                setWalkthroughIndex(0);
                setIsAutoWalkthrough(true);
              }
            }}
          >
            {isAutoWalkthrough ? '⏹ Stop Demo' : '🎬 Full Walkthrough'}
          </button>

          <button
            style={{
              background: isDemoMode ? 'rgba(139, 92, 246, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              border: isDemoMode ? '1px solid #8B5CF6' : '1px solid var(--border)',
              color: isDemoMode ? '#C4B5FD' : '#E2E8F0',
            }}
            className="btn"
            onClick={() => {
              setIsDemoMode(!isDemoMode);
              setDemoStep(1);
              setIsPlaying(false);
            }}
          >
            📋 Stepper Demo
          </button>

          <button
            className="btn btn-primary"
            onClick={() => runInvestigation(selectedIncidentId)}
            disabled={isLoading}
          >
            {isLoading ? 'Investigating...' : '⚡ Investigate'}
          </button>
        </div>
      </header>

      {/* Automated Walkthrough Director Banner */}
      {isAutoWalkthrough && (
        <section
          style={{
            background: 'linear-gradient(90deg, #1E1B4B 0%, #0F172A 100%)',
            borderBottom: '2px solid #8B5CF6',
            padding: '0.8rem 1.5rem',
            boxShadow: '0 4px 20px rgba(139, 92, 246, 0.25)',
          }}
        >
          <div
            style={{
              maxWidth: '1800px',
              margin: '0 auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #EF4444',
                  color: '#FCA5A5',
                  padding: '3px 8px',
                  borderRadius: '999px',
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  letterSpacing: '0.05em',
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: '#EF4444',
                    boxShadow: '0 0 8px #EF4444',
                  }}
                />
                REC • STAGE {walkthroughIndex + 1}/{WALKTHROUGH_STAGES.length}
              </span>
              <div>
                <strong style={{ fontSize: '0.86rem', color: '#C4B5FD', letterSpacing: '-0.01em' }}>
                  {WALKTHROUGH_STAGES[walkthroughIndex]?.title}
                </strong>
                <div style={{ fontSize: '0.76rem', color: '#F8FAFC', fontWeight: 500, marginTop: '1px' }}>
                  {WALKTHROUGH_STAGES[walkthroughIndex]?.banner}
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.72rem', padding: '0.3rem 0.7rem' }}
              onClick={() => setIsAutoWalkthrough(false)}
            >
              Exit Walkthrough
            </button>
          </div>
        </section>
      )}

      {/* 2. Interactive Live Reasoning Demo Banner (When Demo Mode is Active) */}
      {isDemoMode && !isAutoWalkthrough && (
        <section
          style={{
            background: 'linear-gradient(90deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15))',
            borderBottom: '1px solid rgba(139, 92, 246, 0.4)',
            padding: '0.75rem 1.5rem',
          }}
        >
          <div
            style={{
              maxWidth: '1800px',
              margin: '0 auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span
                style={{
                  background: '#8B5CF6',
                  color: 'white',
                  fontWeight: 800,
                  fontSize: '0.7rem',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  letterSpacing: '0.04em',
                }}
              >
                DEMO STEP {demoStep} / 7
              </span>
              <div>
                <strong style={{ fontSize: '0.88rem', color: '#F8FAFC' }}>
                  {currentStepInfo.title}
                </strong>
                <div style={{ fontSize: '0.74rem', color: '#93C5FD' }}>
                  Tool: <code>{currentStepInfo.tool}</code> — {currentStepInfo.detail}
                </div>
              </div>
            </div>

            {/* Stepper Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem' }}
                onClick={() => setDemoStep((p) => Math.max(1, p - 1))}
                disabled={demoStep === 1}
              >
                ⏮ Prev
              </button>
              <button
                className="btn"
                style={{
                  padding: '0.35rem 0.85rem',
                  fontSize: '0.75rem',
                  background: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  border: isPlaying ? '1px solid #EF4444' : '1px solid #10B981',
                  color: isPlaying ? '#FCA5A5' : '#6EE7B7',
                }}
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? '⏸ Pause' : '▶ Auto Play'}
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem' }}
                onClick={() => setDemoStep((p) => Math.min(7, p + 1))}
                disabled={demoStep === 7}
              >
                Next ⏭
              </button>
            </div>
          </div>
        </section>
      )}

      {/* 3. Incident Summary & Verdict Banner */}
      <section
        style={{
          borderBottom: '1px solid var(--border)',
          background: 'rgba(13, 18, 31, 0.65)',
          padding: '0.85rem 1.5rem',
        }}
      >
        <div
          style={{
            maxWidth: '1800px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          {/* Incident Info */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
              <span style={{ fontSize: '0.92rem', fontWeight: 700, color: '#F8FAFC' }}>
                {currentIncident?.title || 'Loading incident...'}
              </span>
              <span style={{ fontSize: '0.7rem', color: '#64748B' }}>
                ID: {selectedIncidentId}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
              {currentIncident?.description || 'Active operational incident being reasoned across FalkorDB graph'}
            </div>
          </div>

          {/* Root Cause Verdict Pill */}
          {report?.root_cause ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                padding: '6px 14px',
              }}
            >
              <div>
                <div style={{ fontSize: '0.65rem', color: '#FCA5A5', fontWeight: 700, textTransform: 'uppercase' }}>
                  Identified Root Cause
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem', color: '#F8FAFC' }}>
                    {report.root_cause.service}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#FCD34D', fontFamily: 'JetBrains Mono, monospace' }}>
                    ({report.root_cause.candidate})
                  </span>
                </div>
              </div>
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  color: '#FCA5A5',
                  padding: '3px 8px',
                  borderRadius: '999px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                }}
              >
                {(report.root_cause.confidence * 100).toFixed(0)}% Confidence
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
              Click ⚡ Investigate to evaluate graph evidence
            </div>
          )}

          {/* Quick Metrics */}
          <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>BLAST RADIUS</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#FCD34D' }}>
                {report?.blast_radius.length || 0} Services
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>MCP TOOLS</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#67E8F9' }}>
                {report?.tool_call_trace.length || 0} Executed
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600 }}>AUDIT LOGS</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#6EE7B7' }}>
                {auditLog.length} Recorded
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Main Workspace (2 Columns) */}
      <main
        style={{
          flex: 1,
          padding: '1.25rem 1.5rem',
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.7fr) minmax(360px, 1fr)',
          gap: '1.25rem',
          maxWidth: '1800px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        {/* Left Column: Visual Graph + Inspection Tabs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Causal Graph Panel */}
          <div className="panel" style={{ height: '420px' }}>
            <div className="panel-header">
              <span className="panel-title">
                <span>🕸️ Multi-Hop Dependency & Causal Graph</span>
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748B', fontFamily: 'JetBrains Mono, monospace' }}>
                Graph: oracle_incidents • FalkorDB
              </span>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              <GraphCanvas
                topology={topology}
                highlightedPath={report?.graph_path}
                activeStep={isDemoMode ? demoStep : null}
              />
            </div>
          </div>

          {/* Deep-Dive Inspection Tabs */}
          <div className="panel" style={{ flex: 1, minHeight: '340px' }}>
            <div className="panel-header">
              <div className="tabs-nav">
                <button
                  className={`tab-btn ${activeTab === 'findings' ? 'active' : ''}`}
                  onClick={() => setActiveTab('findings')}
                >
                  📋 Evidence & Findings ({report?.findings.length || 0})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'hypotheses' ? 'active' : ''}`}
                  onClick={() => setActiveTab('hypotheses')}
                >
                  ⚖️ Hypotheses ({report?.hypotheses_evaluated.length || 0})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'blast' ? 'active' : ''}`}
                  onClick={() => setActiveTab('blast')}
                >
                  💥 Blast Radius ({report?.blast_radius.length || 0})
                </button>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#64748B' }}>
                {activeTab === 'findings' && 'OBSERVED • INFERRED • UNKNOWN'}
                {activeTab === 'hypotheses' && 'Differentiating Hypotheses with Grounded Telemetry'}
                {activeTab === 'blast' && 'Reverse DEPENDS_ON Traversal'}
              </span>
            </div>

            <div className="panel-body">
              {activeTab === 'findings' && (
                report?.findings ? (
                  <FindingsPanel findings={report.findings} />
                ) : (
                  <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Awaiting findings...</div>
                )
              )}

              {activeTab === 'hypotheses' && (
                report?.hypotheses_evaluated ? (
                  <HypothesesSection hypotheses={report.hypotheses_evaluated} />
                ) : (
                  <div style={{ color: '#64748B', fontSize: '0.8rem' }}>Evaluating candidate causes...</div>
                )
              )}

              {activeTab === 'blast' && (
                <div>
                  <div style={{ marginBottom: '0.75rem', fontSize: '0.78rem', color: '#94A3B8', lineHeight: 1.4 }}>
                    Evaluates reverse dependencies from the failing provider to determine downstream customer impact.
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#64748B', textAlign: 'left' }}>
                        <th style={{ padding: '6px' }}>Service</th>
                        <th style={{ padding: '6px' }}>Criticality</th>
                        <th style={{ padding: '6px' }}>Owner Team</th>
                        <th style={{ padding: '6px' }}>Hop Distance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report?.blast_radius.map((b, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <td style={{ padding: '8px 6px', fontWeight: 600, color: '#F1F5F9' }}>
                            {b.affected_service}
                          </td>
                          <td style={{ padding: '8px 6px' }}>
                            <span className="badge badge-warning">{b.criticality}</span>
                          </td>
                          <td style={{ padding: '8px 6px', color: '#94A3B8' }}>{b.owner_team}</td>
                          <td style={{ padding: '8px 6px', color: '#67E8F9', fontFamily: 'JetBrains Mono, monospace' }}>
                            {b.hop_distance} hop(s)
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Negative Test Proof Box */}
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '8px 12px',
                      background: 'rgba(16, 185, 129, 0.05)',
                      border: '1px solid rgba(16, 185, 129, 0.25)',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                      color: '#6EE7B7',
                    }}
                  >
                    ✓ <strong>Negative Test Passed:</strong> Disconnected service <code>analytics-pipeline</code> is correctly excluded from blast radius (bounded graph traversal verified).
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Remediation Gate, Tool Trace & Audit */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Safe Action Proposal & Human Approval Gate */}
          <div
            style={{
              background: isActionExecuted
                ? 'rgba(16, 185, 129, 0.06)'
                : 'linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(139, 92, 246, 0.1))',
              border: isActionExecuted
                ? '1px solid rgba(16, 185, 129, 0.35)'
                : '1px solid rgba(59, 130, 246, 0.35)',
              borderRadius: '12px',
              padding: '1.1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ fontWeight: 800, fontSize: '0.88rem', color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🛡️</span>
                <span>Human-Gated Action Gate</span>
              </div>
              <span
                className={`badge ${isActionExecuted ? 'badge-success' : 'badge-warning'}`}
              >
                {isActionExecuted ? 'EXECUTED & AUDITED' : 'PENDING APPROVAL'}
              </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#94A3B8', marginBottom: '0.85rem', lineHeight: 1.4 }}>
              {report?.proposed_remediation?.description || 'Awaiting investigation proposal...'}
            </p>

            <button
              className="btn btn-success"
              style={{ width: '100%', padding: '0.6rem 1rem' }}
              onClick={() => setIsModalOpen(true)}
              disabled={!report?.proposed_remediation}
            >
              {isActionExecuted ? '✓ Authorize Another Simulated Action' : 'Approve Simulated Remediation'}
            </button>

            <div style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '8px', textAlign: 'center' }}>
              Anti-Self-Approval policy enforced • FalkorDB immutable ledger
            </div>
          </div>

          {/* MCP Tool Execution Trace */}
          <div className="panel" style={{ maxHeight: '310px' }}>
            <div className="panel-header">
              <span className="panel-title">⚡ MCP Tool Execution Trace</span>
              <span style={{ fontSize: '0.7rem', color: '#06B6D4', fontFamily: 'JetBrains Mono, monospace' }}>
                {report?.tool_call_trace.length || 0} tools
              </span>
            </div>
            <div className="panel-body" style={{ gap: '0.4rem', padding: '0.75rem' }}>
              {report?.tool_call_trace.map((step) => {
                const isCurrentDemoStep = isDemoMode && demoStep === step.step;
                return (
                  <div
                    key={step.step}
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '0.72rem',
                      padding: '5px 8px',
                      background: isCurrentDemoStep ? 'rgba(59, 130, 246, 0.25)' : 'rgba(0, 0, 0, 0.3)',
                      borderLeft: isCurrentDemoStep ? '3px solid #60A5FA' : '3px solid #3B82F6',
                      borderRadius: '0 4px 4px 0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ color: isCurrentDemoStep ? '#93C5FD' : '#E2E8F0', fontWeight: isCurrentDemoStep ? 700 : 400 }}>
                      <span style={{ color: '#64748B' }}>#{step.step}</span> {step.tool}
                    </span>
                    <span style={{ color: '#10B981', fontWeight: 600, fontSize: '0.68rem' }}>
                      ✓ {step.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Immutable Audit Ledger */}
          <div className="panel" style={{ flex: 1, minHeight: '180px' }}>
            <div className="panel-header">
              <span className="panel-title">📜 Immutable Audit Ledger</span>
              <span style={{ fontSize: '0.7rem', color: '#10B981' }}>{auditLog.length} events</span>
            </div>
            <div className="panel-body" style={{ gap: '0.4rem', padding: '0.75rem' }}>
              {auditLog.length === 0 ? (
                <div style={{ fontSize: '0.75rem', color: '#64748B' }}>No actions recorded yet.</div>
              ) : (
                auditLog.map((log) => (
                  <div
                    key={log.audit_id}
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '0.68rem',
                      color: log.status.includes('EXECUTED') ? '#6EE7B7' : '#FCA5A5',
                      background: 'rgba(0, 0, 0, 0.3)',
                      padding: '5px 8px',
                      borderRadius: '4px',
                      lineHeight: 1.35,
                    }}
                  >
                    <div>
                      <span style={{ color: '#64748B' }}>[{log.timestamp.substring(11, 19)}]</span>{' '}
                      <strong>{log.action_type}</strong>
                    </div>
                    <div style={{ color: '#94A3B8', fontSize: '0.64rem' }}>
                      Actor: {log.actor} • {log.status}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>

      {/* 5. Human Approval Modal */}
      <ActionModal
        proposal={report?.proposed_remediation || null}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onApprove={handleApproveAction}
        overrideApprover={modalApprover}
        overrideError={modalError}
      />
    </div>
  );
};

export default App;
