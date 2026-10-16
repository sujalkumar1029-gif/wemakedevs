import React, { useState } from 'react';
import type { ProposedRemediation } from '../types';

interface ActionModalProps {
  proposal: ProposedRemediation | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (actionId: string, approver: string, notes: string) => Promise<void>;
}

export const ActionModal: React.FC<ActionModalProps> = ({ proposal, isOpen, onClose, onApprove }) => {
  const [approver, setApprover] = useState('Sarah Connor (Staff SRE)');
  const [notes, setNotes] = useState('Verified connection pool leak in telemetry. Rollback confirmed.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !proposal) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (approver.toLowerCase().includes('agent')) {
      setError('Policy violation: ORACLE Agent cannot approve its own proposals. Please enter a human engineer name.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onApprove(proposal.action_id, approver, notes);
      setIsSubmitting(false);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Approval execution failed.');
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: '#0E131F',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: '12px',
        width: '520px',
        maxWidth: '92vw',
        padding: '1.5rem',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.6)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#F1F5F9' }}>🛡️ Human Approval Policy Gate</h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#64748B', fontSize: '1.2rem', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>

        <div style={{
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: '8px',
          padding: '0.85rem',
          fontSize: '0.8rem',
          color: '#93C5FD',
          marginBottom: '1rem',
          lineHeight: 1.4
        }}>
          <strong>Action:</strong> {proposal.action_type}<br />
          <strong>Target:</strong> {proposal.target_id}<br />
          <strong>Evidence Grounded:</strong> {proposal.evidence_ids.join(', ')}<br />
          <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
            Note: All remediation actions are simulated in a safe test environment. Real infrastructure commands are blocked.
          </span>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '6px',
            padding: '0.6rem 0.8rem',
            color: '#FCA5A5',
            fontSize: '0.78rem',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '0.35rem' }}>
              Human Approver Identifier
            </label>
            <input
              type="text"
              required
              value={approver}
              onChange={(e) => setApprover(e.target.value)}
              placeholder="e.g. Sarah Connor (Staff SRE)"
              style={{
                width: '100%',
                padding: '0.6rem 0.8rem',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: 'white',
                fontFamily: 'inherit',
                fontSize: '0.85rem'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '0.35rem' }}>
              Approval Justification / Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem 0.8rem',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: 'white',
                fontFamily: 'inherit',
                fontSize: '0.85rem',
                resize: 'none'
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
              {isSubmitting ? 'Simulating...' : 'Authorize Simulated Action'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
