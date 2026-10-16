import React from 'react';
import type { Hypothesis } from '../types';

interface HypothesesSectionProps {
  hypotheses: Hypothesis[];
}

export const HypothesesSection: React.FC<HypothesesSectionProps> = ({ hypotheses }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {hypotheses.map((h) => {
        const isConfirmed = h.status === 'CONFIRMED_ROOT_CAUSE';
        return (
          <div
            key={h.hypothesis_id}
            style={{
              padding: '0.85rem',
              borderRadius: '8px',
              background: isConfirmed ? 'rgba(239, 68, 68, 0.05)' : 'rgba(255, 255, 255, 0.02)',
              border: isConfirmed ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <strong style={{ fontSize: '0.85rem', color: isConfirmed ? '#FCA5A5' : '#E2E8F0' }}>
                {h.name}
              </strong>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: isConfirmed ? 'rgba(239, 68, 68, 0.2)' : 'rgba(148, 163, 184, 0.15)',
                  color: isConfirmed ? '#EF4444' : '#94A3B8',
                  border: isConfirmed ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(148, 163, 184, 0.3)',
                }}
              >
                {h.status}
              </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#94A3B8', lineHeight: 1.35, margin: '0 0 0.5rem 0' }}>
              {h.reasoning}
            </p>

            {h.counter_evidence && (
              <div style={{
                background: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '0.72rem',
                color: '#FCD34D',
                marginBottom: '0.5rem'
              }}>
                <strong>Counterevidence:</strong> {h.counter_evidence}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: '#64748B' }}>
              <span>
                Evidence: <span style={{ color: '#06B6D4', fontFamily: 'monospace' }}>{h.supporting_evidence_ids.join(', ')}</span>
              </span>
              <span style={{ fontWeight: 700, color: isConfirmed ? '#EF4444' : '#64748B' }}>
                Confidence: {(h.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
