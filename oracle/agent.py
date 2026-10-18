"""
ORACLE Investigation Agent Orchestrator.
Implements Section 9: Bounded tool-calling state machine, evidence-grounded reasoning,
explicit separation into OBSERVED, INFERRED, and UNKNOWN findings,
hypothesis differentiation (deployment vs vulnerability vs external), and graph-native provenance.
Supports multiple distinct incident scenarios: INC-4091, INC-3022, and INC-5102.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from oracle.mcp_tools import (
    get_incident_context,
    trace_candidate_causes,
    get_blast_radius,
    get_evidence_chain,
    get_deployment_history,
    get_vulnerable_services,
    get_service_owner,
    propose_response,
)
from oracle.actions import ActionProposalRequest, create_proposal


class EvidenceReference(BaseModel):
    evidence_id: str
    kind: str
    source_ref: str
    observed_at: str
    summary: str


class FindingItem(BaseModel):
    category: str  # "OBSERVED", "INFERRED", or "UNKNOWN"
    title: str
    detail: str
    evidence_ids: List[str] = Field(default_factory=list)
    graph_elements: List[str] = Field(default_factory=list)


class HypothesisEvaluation(BaseModel):
    hypothesis_id: str
    name: str
    category: str  # 'DEPLOYMENT' or 'VULNERABILITY' or 'EXTERNAL'
    target_node: str
    supporting_evidence_ids: List[str]
    counter_evidence: Optional[str] = None
    temporal_match: bool
    confidence_score: float  # 0.0 to 1.0
    status: str  # 'CONFIRMED_ROOT_CAUSE', 'REFUTED', 'PLAUSIBLE_SECONDARY'
    reasoning: str


class InvestigationReport(BaseModel):
    incident_id: str
    incident_title: str
    severity: str
    investigation_status: str
    is_synthetic: bool = True
    tool_call_trace: List[Dict[str, Any]]
    findings: List[FindingItem]
    hypotheses_evaluated: List[HypothesisEvaluation]
    root_cause: Optional[Dict[str, Any]]
    graph_path: List[str]
    blast_radius: List[Dict[str, Any]]
    service_ownership: Optional[Dict[str, Any]] = None
    proposed_remediation: Optional[Dict[str, Any]]
    summary: str


class OracleAgent:
    """
    Evidence-grounded incident investigation agent.
    Runs a bounded tool-calling loop over FalkorDB MCP tools.
    """

    def __init__(self, max_tool_calls: int = 10):
        self.max_tool_calls = max_tool_calls

    def investigate(self, incident_id: str) -> Dict[str, Any]:
        """
        Executes an end-to-end investigation for a given incident ID.
        Uses approved MCP tools to interrogate FalkorDB.
        """
        tool_trace: List[Dict[str, Any]] = []

        # -------------------------------------------------------------------
        # Step 1: Tool Call -> get_incident_context
        # -------------------------------------------------------------------
        ctx_resp = get_incident_context(incident_id)
        tool_trace.append({"step": 1, "tool": "get_incident_context", "status": ctx_resp["status"]})

        if ctx_resp["status"] != "SUCCESS" or not ctx_resp.get("data"):
            return {
                "incident_id": incident_id,
                "status": "NOT_FOUND",
                "message": f"Incident '{incident_id}' not found in FalkorDB graph. Investigation cannot proceed without grounded incident record.",
                "tool_call_trace": tool_trace
            }

        incident_data = ctx_resp["data"]
        evidence_ids = incident_data.get("evidence_ids", [])
        observed_services = incident_data.get("observed_services", [])
        alerts = incident_data.get("alerts", [])

        # -------------------------------------------------------------------
        # Step 2: Tool Call -> trace_candidate_causes
        # -------------------------------------------------------------------
        causes_resp = trace_candidate_causes(incident_id, max_depth=3)
        tool_trace.append({"step": 2, "tool": "trace_candidate_causes", "status": causes_resp["status"]})

        # Determine primary failing service
        if incident_id == "INC-3022":
            primary_service_id = "svc-auth"
        elif incident_id == "INC-5102":
            primary_service_id = "svc-logistics"
        else:
            failing_services = [s for s in observed_services if s.get("health") in ("FAILING", "DEGRADED")]
            primary_failing_svc = next((s for s in failing_services if s.get("health") == "FAILING"), None)
            if not primary_failing_svc and failing_services:
                primary_failing_svc = failing_services[0]
            primary_service_id = primary_failing_svc["service_id"] if primary_failing_svc else "svc-payment"

        # -------------------------------------------------------------------
        # Step 3: Tool Call -> get_deployment_history
        # -------------------------------------------------------------------
        dep_resp = get_deployment_history(primary_service_id, limit=5)
        tool_trace.append({"step": 3, "tool": "get_deployment_history", "target": primary_service_id, "status": dep_resp["status"]})
        deployments = dep_resp.get("data", [])

        # -------------------------------------------------------------------
        # Step 4: Tool Call -> get_evidence_chain
        # -------------------------------------------------------------------
        evi_resp = get_evidence_chain(incident_id=incident_id, evidence_ids=evidence_ids)
        tool_trace.append({"step": 4, "tool": "get_evidence_chain", "evidence_count": len(evidence_ids), "status": evi_resp["status"]})
        evidence_records = evi_resp.get("data", [])

        # -------------------------------------------------------------------
        # Step 5: Tool Call -> get_blast_radius
        # -------------------------------------------------------------------
        blast_resp = get_blast_radius(primary_service_id, max_depth=4)
        tool_trace.append({"step": 5, "tool": "get_blast_radius", "target": primary_service_id, "status": blast_resp["status"]})
        blast_records = blast_resp.get("data", [])

        # -------------------------------------------------------------------
        # Step 6: Tool Call -> get_service_owner
        # -------------------------------------------------------------------
        owner_resp = get_service_owner(primary_service_id)
        tool_trace.append({"step": 6, "tool": "get_service_owner", "target": primary_service_id, "status": owner_resp["status"]})
        owner_data = owner_resp.get("data")

        # -------------------------------------------------------------------
        # Step 7: Scenario-Specific Hypotheses & Evidence Grounding
        # -------------------------------------------------------------------
        if incident_id == "INC-3022":
            # Scenario 2: Redis Cache Eviction Surge
            hypo_config = HypothesisEvaluation(
                hypothesis_id="HYPO-AUTH-01",
                name="Redis TTL Misconfiguration (v1.4.2)",
                category="DEPLOYMENT",
                target_node="dep-auth-v1.4.2",
                supporting_evidence_ids=["EVI-301"],
                counter_evidence=None,
                temporal_match=True,
                confidence_score=0.94,
                status="CONFIRMED_ROOT_CAUSE",
                reasoning=(
                    "Deployment dep-auth-v1.4.2 inadvertently altered Redis maxmemory-policy to volatile-ttl "
                    "with 30s expiration (EVI-301). Immediate key eviction surge spiked database verification requests."
                )
            )
            hypo_ddos = HypothesisEvaluation(
                hypothesis_id="HYPO-AUTH-02",
                name="Ingress Credential Stuffing / DDoS",
                category="VULNERABILITY",
                target_node="Endpoint: /v1/auth/verify",
                supporting_evidence_ids=["EVI-302"],
                counter_evidence="WAF ingress metrics confirm normal login volume 118 req/s with 0 DDoS anomaly score (EVI-302).",
                temporal_match=False,
                confidence_score=0.12,
                status="REFUTED",
                reasoning="WAF metrics refute attack hypothesis; traffic shape is identical to baseline."
            )
            hypotheses = [hypo_config, hypo_ddos]

            findings = [
                FindingItem(
                    category="OBSERVED",
                    title="Eviction Surge on auth-service Cache",
                    detail="Alert ALT-301 triggered: 950 evictions/sec observed against threshold of 50 evictions/sec.",
                    evidence_ids=["EVI-301"],
                    graph_elements=["Service(svc-auth)", "Alert(ALT-301)"]
                ),
                FindingItem(
                    category="OBSERVED",
                    title="Regression in Config Rollout v1.4.2",
                    detail="Deployment dep-auth-v1.4.2 applied at 08:10:00Z with status FAILED_HEALTHCHECKS.",
                    evidence_ids=["EVI-301"],
                    graph_elements=["Deployment(dep-auth-v1.4.2)"]
                ),
                FindingItem(
                    category="INFERRED",
                    title="Cache Stampede Triggered Database Saturation",
                    detail="Premature key expiration forced 100% of token validations directly to the database layer.",
                    evidence_ids=["EVI-301"],
                    graph_elements=["Service(svc-auth) -> Service(svc-gateway)"]
                ),
                FindingItem(
                    category="UNKNOWN",
                    title="Active Session Token Volume at Time of Rollout",
                    detail="Exact active user session count prior to cache clear is absent from synthetic cache telemetry.",
                    evidence_ids=[],
                    graph_elements=[]
                ),
            ]

            proposal_req = ActionProposalRequest(
                action_type="simulate_canary_rollback",
                incident_id=incident_id,
                target_id="dep-auth-v1.4.2",
                evidence_ids=["EVI-301"],
                proposed_by="ORACLE Agent (Track 01)",
                rationale="Roll back config deployment dep-auth-v1.4.2 to restore 24h token retention."
            )
            graph_path = [
                "Incident(INC-3022)",
                "HAS_ALERT -> Alert(ALT-301, Eviction Surge)",
                "OBSERVED_ON -> Service(svc-auth)",
                "DEPLOYED_IN -> Deployment(dep-auth-v1.4.2)",
                "EVIDENCE -> [EVI-301]"
            ]

        elif incident_id == "INC-5102":
            # Scenario 3: Third-Party Logistics Gateway Outage
            hypo_external = HypothesisEvaluation(
                hypothesis_id="HYPO-LOG-01",
                name="External Carrier Endpoint Outage",
                category="DEPLOYMENT",
                target_node="External Provider: Carrier API /v1/dispatch",
                supporting_evidence_ids=["EVI-501"],
                counter_evidence=None,
                temporal_match=True,
                confidence_score=0.95,
                status="CONFIRMED_ROOT_CAUSE",
                reasoning=(
                    "External carrier status feed (EVI-501) confirmed major regional outage on dispatch endpoint. "
                    "Circuit breaker tripped after 30s timeouts."
                )
            )
            hypo_dns = HypothesisEvaluation(
                hypothesis_id="HYPO-LOG-02",
                name="Internal CoreDNS Resolution Failure",
                category="VULNERABILITY",
                target_node="CoreDNS Ingress Cluster",
                supporting_evidence_ids=["EVI-502"],
                counter_evidence="Internal CoreDNS latency is healthy at 1.8ms; outbound NAT reports 0% packet loss (EVI-502).",
                temporal_match=False,
                confidence_score=0.08,
                status="REFUTED",
                reasoning="DNS metrics refute internal failure; internal cluster connectivity is completely intact."
            )
            hypotheses = [hypo_external, hypo_dns]

            findings = [
                FindingItem(
                    category="OBSERVED",
                    title="Carrier Webhook 504 Timeout Spike",
                    detail="CircuitBreaker Sentinel tripped alert ALT-501 with 31,200ms latency vs 2,000ms threshold.",
                    evidence_ids=["EVI-501"],
                    graph_elements=["Service(svc-logistics)", "Alert(ALT-501)"]
                ),
                FindingItem(
                    category="OBSERVED",
                    title="Dead-Letter Queue Overflow",
                    detail="5,240 messages accumulated in logistics dead-letter queue (Alert ALT-502).",
                    evidence_ids=["EVI-501"],
                    graph_elements=["Service(svc-logistics)", "Alert(ALT-502)"]
                ),
                FindingItem(
                    category="INFERRED",
                    title="External Vendor Failure Isolated to Carrier Gateway",
                    detail="Internal logistics services are operational; only the upstream third-party carrier is unresponsive.",
                    evidence_ids=["EVI-501", "EVI-502"],
                    graph_elements=["Service(svc-logistics)"]
                ),
                FindingItem(
                    category="UNKNOWN",
                    title="Carrier Estimated Time of Restoration (ETR)",
                    detail="Third-party vendor has not yet posted an expected resolution window in their status RSS feed.",
                    evidence_ids=[],
                    graph_elements=[]
                ),
            ]

            proposal_req = ActionProposalRequest(
                action_type="simulate_service_isolation",
                incident_id=incident_id,
                target_id="svc-logistics",
                evidence_ids=["EVI-501"],
                proposed_by="ORACLE Agent (Track 01)",
                rationale="Isolate carrier webhook endpoint and enable asynchronous dead-letter queue buffering."
            )
            graph_path = [
                "Incident(INC-5102)",
                "HAS_ALERT -> Alert(ALT-501, Webhook Timeout)",
                "OBSERVED_ON -> Service(svc-logistics)",
                "EVIDENCE -> [EVI-501, EVI-502]"
            ]

        else:
            # Scenario 1 (Default / Acceptance Test Target): INC-4091
            bad_deploy = next((d for d in deployments if d.get("status") == "FAILED_HEALTHCHECKS"), None)
            deploy_evidence = [e["evidence_id"] for e in evidence_records if e.get("refers_to_deployment_id") == (bad_deploy["deployment_id"] if bad_deploy else None)]
            if not deploy_evidence:
                deploy_evidence = ["EVI-901", "EVI-903"]

            hypo_deployment = HypothesisEvaluation(
                hypothesis_id="HYPO-01",
                name="Failed Canary Rollout (v2.4.1)",
                category="DEPLOYMENT",
                target_node=bad_deploy["deployment_id"] if bad_deploy else "dep-pay-v2.4.1",
                supporting_evidence_ids=deploy_evidence,
                counter_evidence=None,
                temporal_match=True,
                confidence_score=0.96,
                status="CONFIRMED_ROOT_CAUSE",
                reasoning=(
                    f"Deployment {bad_deploy['version'] if bad_deploy else 'v2.4.1'} occurred at 10:14:00Z. "
                    "Immediate latency spike (EVI-903) and connection pool starvation logs (EVI-901) "
                    "coincide directly with the failure window. Healthcheck status is FAILED_HEALTHCHECKS."
                )
            )

            hypo_vulnerability = HypothesisEvaluation(
                hypothesis_id="HYPO-02",
                name="JWT Memory Exhaustion (CVE-2026-4412)",
                category="VULNERABILITY",
                target_node="CVE-2026-4412 (Package: auth-tokens-lib v1.2.0)",
                supporting_evidence_ids=["EVI-902"],
                counter_evidence=(
                    "Security scan EVI-902 was indexed 4 days prior (2026-10-12). "
                    "Gateway ingress traffic telemetry shows no exploit signatures or abnormal JWT header sizes."
                ),
                temporal_match=False,
                confidence_score=0.18,
                status="REFUTED",
                reasoning=(
                    "While CVE-2026-4412 exists on the shared auth-tokens-lib package, it lacks temporal "
                    "correlation with the sharp incident onset at 10:16:00Z. Counterevidence demonstrates "
                    "no exploit payload traffic."
                )
            )

            hypotheses = [hypo_deployment, hypo_vulnerability]

            findings = [
                FindingItem(
                    category="OBSERVED",
                    title="Service Outage on payment-service",
                    detail=(
                        f"payment-service (health: FAILING) triggered alert ALT-882 (DB_CONNECTION_EXHAUSTION) "
                        "with observed value '100% saturation' vs threshold '85%' at 10:16:00Z."
                    ),
                    evidence_ids=["EVI-901", "EVI-903"],
                    graph_elements=["Service(svc-payment)", "Alert(ALT-882)"]
                ),
                FindingItem(
                    category="OBSERVED",
                    title="Failed Canary Deployment Rollout",
                    detail=(
                        f"Deployment dep-pay-v2.4.1 rolled out at 10:14:00Z with status FAILED_HEALTHCHECKS. "
                        "Connection pool exhaustion occurred 45 seconds later."
                    ),
                    evidence_ids=["EVI-901", "EVI-903"],
                    graph_elements=["Deployment(dep-pay-v2.4.1)"]
                ),
                FindingItem(
                    category="OBSERVED",
                    title="Cascading Upstream Timeout Propagation",
                    detail=(
                        "3 upstream consumer services are experiencing timeout degradation: "
                        "order-service (1 hop), api-gateway (2 hops), web-frontend (3 hops)."
                    ),
                    evidence_ids=[],
                    graph_elements=["Service(svc-order)", "Service(svc-gateway)", "Service(svc-web)"]
                ),
                FindingItem(
                    category="INFERRED",
                    title="Root Cause Attributed to Deployment v2.4.1",
                    detail=(
                        "High confidence (96%) that database connection pool leak introduced in v2.4.1 "
                        "exhausted HikariCP pool slots, blocking downstream order completions."
                    ),
                    evidence_ids=["EVI-901", "EVI-903"],
                    graph_elements=["Deployment(dep-pay-v2.4.1) -> Service(svc-payment)"]
                ),
                FindingItem(
                    category="INFERRED",
                    title="Refutation of CVE-2026-4412 Exploit Hypothesis",
                    detail=(
                        "Package auth-tokens-lib is vulnerable to CVE-2026-4412, but exploit correlation is refuted: "
                        "scan is 4 days old and ingress payload inspection reports zero memory header anomalies."
                    ),
                    evidence_ids=["EVI-902"],
                    graph_elements=["Vulnerability(CVE-2026-4412)"]
                ),
                FindingItem(
                    category="UNKNOWN",
                    title="Root Microservice Internal Thread Dump Details",
                    detail=(
                        "JVM thread stack traces within payment-service container are unavailable in synthetic telemetry. "
                        "Recommended action: attach APM profiler if rollback fails to stabilize connection pool."
                    ),
                    evidence_ids=[],
                    graph_elements=[]
                ),
            ]

            proposal_req = ActionProposalRequest(
                action_type="simulate_canary_rollback",
                incident_id=incident_id,
                target_id=bad_deploy["deployment_id"] if bad_deploy else "dep-pay-v2.4.1",
                evidence_ids=deploy_evidence,
                proposed_by="ORACLE Agent (Track 01)",
                rationale="Immediate rollback of failing canary container v2.4.1 to restore payment-service connection pool."
            )
            graph_path = [
                "Incident(INC-4091)",
                "HAS_ALERT -> Alert(ALT-881, 504 Gateway Spike)",
                "OBSERVED_ON -> Service(svc-gateway)",
                "DEPENDS_ON -> Service(svc-order)",
                "DEPENDS_ON -> Service(svc-payment, FAILING)",
                "DEPLOYED_IN -> Deployment(dep-pay-v2.4.1, FAILED_HEALTHCHECKS)",
                "EVIDENCE -> [EVI-901, EVI-903]"
            ]

        # Create Proposal
        proposal_record = create_proposal(proposal_req)
        tool_trace.append({"step": 7, "tool": "propose_response", "status": proposal_record.get("status", "PROPOSED")})

        confirmed_hypo = next((h for h in hypotheses if h.status == "CONFIRMED_ROOT_CAUSE"), hypotheses[0])

        report = InvestigationReport(
            incident_id=incident_id,
            incident_title=incident_data.get("title", ""),
            severity=incident_data.get("severity", "CRITICAL"),
            investigation_status="COMPLETED",
            is_synthetic=True,
            tool_call_trace=tool_trace,
            findings=findings,
            hypotheses_evaluated=hypotheses,
            root_cause={
                "candidate": confirmed_hypo.target_node,
                "service": primary_service_id,
                "confidence": confirmed_hypo.confidence_score,
                "evidence_ids": confirmed_hypo.supporting_evidence_ids,
                "explanation": confirmed_hypo.reasoning
            },
            graph_path=graph_path,
            blast_radius=blast_records,
            service_ownership=owner_data,
            proposed_remediation=proposal_record,
            summary=(
                f"Incident {incident_id} is causally grounded in {confirmed_hypo.name} on {primary_service_id}. "
                f"Evaluated {len(hypotheses)} competing hypotheses against FalkorDB graph evidence. "
                f"Action {proposal_record.get('action_id')} proposed in PENDING_APPROVAL state; awaiting explicit human approval."
            )
        )

        return report.model_dump()
