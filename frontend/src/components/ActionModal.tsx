import React, { useState } from 'react';
import type { ProposedRemediation } from '../types';

interface ActionModalProps {
  proposal: ProposedRemediation | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (actionId: string, approver: string, notes: string) => Promise<void>;
  overrideApprover?: string;
  overrideError?: string | null;
}

export const ActionModal: React.FC<ActionModalProps> = ({
  proposal,
  isOpen,
  onClose,
  onApprove,
  overrideApprover,
  overrideError,
}) => {
  const [approver, setApprover] = useState('Sarah Connor (Staff SRE)');
  const [notes, setNotes] = useState('Verified connection pool starvation in telemetry. Rollback approved.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (overrideApprover !== undefined) {
      setApprover(overrideApprover);
    }
  }, [overrideApprover]);

  React.useEffect(() => {
    if (overrideError !== undefined) {
      setError(overrideError);
    }
  }, [overrideError]);

  const activeProposal = proposal || {
    action_id: 'act-sim-4091-rollback',
    action_type: 'simulate_canary_rollback',
    target_id: 'payment-service',
    description: 'Simulate rolling back candidate failed deployment to stable baseline.',
    evidence_ids: ['EVI-901', 'EVI-903'],
    requires_human_approval: true,
    status: 'PENDING_APPROVAL',
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (approver.toLowerCase().includes('agent')) {
      setError('Policy violation: ORACLE Agent cannot approve its own proposals (Anti-Self-Approval policy). Please enter a human engineer name.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onApprove(activeProposal.action_id, approver, notes);
      setIsSubmitting(false);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Approval execution failed.');
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: '#0D131F',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '12px',
          width: '520px',
          maxWidth: '100%',
          padding: '1.4rem',
          boxShadow: '0 25px 50px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>🛡️</span>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#F8FAFC' }}>
              Human Approval Policy Gate
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748B',
              fontSize: '1.3rem',
              cursor: 'pointer',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Action Details Card */}
        <div
          style={{
            background: 'rgba(59, 130, 246, 0.06)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '8px',
            padding: '0.8rem',
            fontSize: '0.78rem',
            color: '#CBD5E1',
            marginBottom: '1rem',
            lineHeight: 1.45,
          }}
        >
          <div>
            <span style={{ color: '#64748B' }}>Action:</span>{' '}
            <strong style={{ color: '#93C5FD' }}>{activeProposal.action_type}</strong>
          </div>
          <div>
            <span style={{ color: '#64748B' }}>Target Service:</span>{' '}
            <strong style={{ color: '#F8FAFC' }}>{activeProposal.target_id}</strong>
          </div>
          <div>
            <span style={{ color: '#64748B' }}>Evidence Grounding:</span>{' '}
            <span style={{ color: '#06B6D4', fontFamily: 'JetBrains Mono, monospace' }}>
              {activeProposal.evidence_ids.join(', ')}
            </span>
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '6px' }}>
            ✓ Non-destructive simulation: executes in synthetic test environment with audit trail.
          </div>
        </div>

        {error && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '0.6rem 0.8rem',
              color: '#FCA5A5',
              fontSize: '0.78rem',
              marginBottom: '1rem',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#CBD5E1' }}>
                Human Approver Name
              </label>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  type="button"
                  onClick={() => setApprover('Sarah Connor (Staff SRE)')}
                  style={{
                    fontSize: '0.65rem',
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '4px',
                    color: '#94A3B8',
                    cursor: 'pointer',
                    padding: '1px 5px',
                  }}
                >
                  SRE Lead
                </button>
                <button
                  type="button"
                  onClick={() => setApprover('Alex Murphy (Traffic Lead)')}
                  style={{
                    fontSize: '0.65rem',
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '4px',
                    color: '#94A3B8',
                    cursor: 'pointer',
                    padding: '1px 5px',
                  }}
                >
                  Traffic Lead
                </button>
              </div>
            </div>
            <input
              type="text"
              required
              value={approver}
              onChange={(e) => setApprover(e.target.value)}
              placeholder="e.g. Sarah Connor (Staff SRE)"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: 'white',
                fontFamily: 'inherit',
                fontSize: '0.82rem',
              }}
            />
          </div>

          <div style={{ marginBottom: '1.1rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '0.35rem' }}>
              Approval Justification & Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: 'white',
                fontFamily: 'inherit',
                fontSize: '0.82rem',
                resize: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-success"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Simulating...' : 'Authorize Simulation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
