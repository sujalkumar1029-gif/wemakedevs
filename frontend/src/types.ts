export interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  created_at: string;
  is_synthetic: boolean;
  alert_count?: number;
  description?: string;
}

export interface Alert {
  alert_id: string;
  signal: string;
  alert_type: string;
  observed_value: string;
  threshold: string;
  timestamp: string;
  source: string;
  service_id?: string;
  service_name?: string;
}

export interface Finding {
  category: 'OBSERVED' | 'INFERRED' | 'UNKNOWN';
  title: string;
  detail: string;
  evidence_ids: string[];
  graph_elements: string[];
}

export interface Hypothesis {
  hypothesis_id: string;
  name: string;
  category: 'DEPLOYMENT' | 'VULNERABILITY';
  target_node: string;
  supporting_evidence_ids: string[];
  counter_evidence?: string | null;
  temporal_match: boolean;
  confidence_score: number;
  status: string;
  reasoning: string;
}

export interface BlastRadiusItem {
  affected_service_id: string;
  affected_service: string;
  criticality: string;
  current_health: string;
  owner_team: string;
  hop_distance: number;
}

export interface ToolTraceItem {
  step: number;
  tool: string;
  status: string;
  target?: string;
  evidence_count?: number;
}

export interface ProposedRemediation {
  action_id: string;
  action_type: string;
  description: string;
  incident_id: string;
  target_id: string;
  evidence_ids: string[];
  state: string;
  proposed_by: string;
  rationale?: string;
  created_at: string;
  status?: string;
}

export interface InvestigationReport {
  incident_id: string;
  incident_title: string;
  severity: string;
  investigation_status: string;
  is_synthetic: boolean;
  tool_call_trace: ToolTraceItem[];
  findings: Finding[];
  hypotheses_evaluated: Hypothesis[];
  root_cause?: {
    candidate: string;
    service: string;
    confidence: number;
    evidence_ids: string[];
    explanation: string;
  };
  graph_path: string[];
  blast_radius: BlastRadiusItem[];
  service_ownership?: {
    service_id: string;
    service_name: string;
    team_name: string;
    on_call: string;
  };
  proposed_remediation?: ProposedRemediation;
  summary: string;
}

export interface AuditRecord {
  audit_id: string;
  action_id: string;
  timestamp: string;
  incident_id: string;
  action_type: string;
  target_id: string;
  status: string;
  actor: string;
  notes?: string;
  outcome?: any;
  is_synthetic: boolean;
}

export interface GraphTopology {
  nodes: Array<{
    id: string;
    label: string;
    properties: Record<string, any>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    relationship: string;
  }>;
}
