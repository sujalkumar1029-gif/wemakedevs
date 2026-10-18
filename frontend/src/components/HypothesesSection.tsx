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
        const isRefuted = h.status === 'REFUTED';

        return (
          <div
            key={h.hypothesis_id}
            style={{
              padding: '0.85rem 1rem',
              borderRadius: '8px',
              background: isConfirmed
                ? 'rgba(239, 68, 68, 0.05)'
                : 'rgba(255, 255, 255, 0.02)',
              border: isConfirmed
                ? '1px solid rgba(239, 68, 68, 0.35)'
                : isRefuted
                ? '1px solid rgba(255, 255, 255, 0.07)'
                : '1px solid rgba(245, 158, 11, 0.3)',
              transition: 'all 0.15s ease',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.4rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: isConfirmed ? '#EF4444' : '#64748B',
                    boxShadow: isConfirmed ? '0 0 8px #EF4444' : 'none',
                  }}
                />
                <strong style={{ fontSize: '0.85rem', color: isConfirmed ? '#FCA5A5' : '#E2E8F0' }}>
                  {h.name}
                </strong>
              </div>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: isConfirmed
                    ? 'rgba(239, 68, 68, 0.2)'
                    : 'rgba(148, 163, 184, 0.12)',
                  color: isConfirmed ? '#FCA5A5' : '#94A3B8',
                  border: isConfirmed
                    ? '1px solid rgba(239, 68, 68, 0.4)'
                    : '1px solid rgba(148, 163, 184, 0.25)',
                }}
              >
                {isConfirmed ? 'CONFIRMED ROOT CAUSE' : h.status}
              </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#94A3B8', lineHeight: 1.4, margin: '0 0 0.5rem 0' }}>
              {h.reasoning}
            </p>

            {/* Counterevidence Alert Box */}
            {h.counter_evidence && (
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.06)',
                  border: '1px solid rgba(245, 158, 11, 0.22)',
                  borderRadius: '6px',
                  padding: '6px 9px',
                  fontSize: '0.72rem',
                  color: '#FCD34D',
                  marginBottom: '0.55rem',
                  lineHeight: 1.35,
                }}
              >
                <strong>Counterevidence:</strong> {h.counter_evidence}
              </div>
            )}

            {/* Confidence Progress Meter */}
            <div style={{ marginTop: '0.4rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.68rem',
                  color: '#64748B',
                  marginBottom: '3px',
                }}
              >
                <span>
                  Evidence ID:{' '}
                  <span style={{ color: '#06B6D4', fontFamily: 'JetBrains Mono, monospace' }}>
                    {h.supporting_evidence_ids.join(', ')}
                  </span>
                </span>
                <span style={{ fontWeight: 700, color: isConfirmed ? '#EF4444' : '#94A3B8' }}>
                  Confidence: {(h.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  background: 'rgba(255, 255, 255, 0.06)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${Math.round(h.confidence_score * 100)}%`,
                    height: '100%',
                    background: isConfirmed ? 'linear-gradient(90deg, #F87171, #EF4444)' : '#64748B',
                    borderRadius: '2px',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
