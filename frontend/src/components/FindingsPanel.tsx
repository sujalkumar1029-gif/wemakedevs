import React, { useState } from 'react';
import type { Finding } from '../types';

interface FindingsPanelProps {
  findings: Finding[];
}

export const FindingsPanel: React.FC<FindingsPanelProps> = ({ findings }) => {
  const [filter, setFilter] = useState<'ALL' | 'OBSERVED' | 'INFERRED' | 'UNKNOWN'>('ALL');

  const filteredFindings = findings.filter(
    (f) => filter === 'ALL' || f.category === filter
  );

  const getBadgeStyle = (category: string) => {
    switch (category) {
      case 'OBSERVED':
        return {
          bg: 'rgba(16, 185, 129, 0.12)',
          text: '#6EE7B7',
          border: 'rgba(16, 185, 129, 0.3)',
          label: 'Direct Telemetry',
        };
      case 'INFERRED':
        return {
          bg: 'rgba(139, 92, 246, 0.12)',
          text: '#C4B5FD',
          border: 'rgba(139, 92, 246, 0.3)',
          label: 'Causal Inference',
        };
      case 'UNKNOWN':
        return {
          bg: 'rgba(245, 158, 11, 0.12)',
          text: '#FCD34D',
          border: 'rgba(245, 158, 11, 0.3)',
          label: 'Telemetry Gap',
        };
      default:
        return {
          bg: 'rgba(255, 255, 255, 0.08)',
          text: '#F1F5F9',
          border: 'rgba(255, 255, 255, 0.15)',
          label: category,
        };
    }
  };

  const countObserved = findings.filter((f) => f.category === 'OBSERVED').length;
  const countInferred = findings.filter((f) => f.category === 'INFERRED').length;
  const countUnknown = findings.filter((f) => f.category === 'UNKNOWN').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Category Filter Pills */}
      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setFilter('ALL')}
          style={{
            padding: '3px 9px',
            fontSize: '0.72rem',
            fontWeight: 600,
            borderRadius: '999px',
            border: filter === 'ALL' ? '1px solid #3B82F6' : '1px solid rgba(255,255,255,0.08)',
            background: filter === 'ALL' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.02)',
            color: filter === 'ALL' ? '#93C5FD' : '#94A3B8',
            cursor: 'pointer',
          }}
        >
          All ({findings.length})
        </button>
        <button
          onClick={() => setFilter('OBSERVED')}
          style={{
            padding: '3px 9px',
            fontSize: '0.72rem',
            fontWeight: 600,
            borderRadius: '999px',
            border: filter === 'OBSERVED' ? '1px solid #10B981' : '1px solid rgba(255,255,255,0.08)',
            background: filter === 'OBSERVED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.02)',
            color: filter === 'OBSERVED' ? '#6EE7B7' : '#94A3B8',
            cursor: 'pointer',
          }}
        >
          Observed ({countObserved})
        </button>
        <button
          onClick={() => setFilter('INFERRED')}
          style={{
            padding: '3px 9px',
            fontSize: '0.72rem',
            fontWeight: 600,
            borderRadius: '999px',
            border: filter === 'INFERRED' ? '1px solid #8B5CF6' : '1px solid rgba(255,255,255,0.08)',
            background: filter === 'INFERRED' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.02)',
            color: filter === 'INFERRED' ? '#C4B5FD' : '#94A3B8',
            cursor: 'pointer',
          }}
        >
          Inferred ({countInferred})
        </button>
        <button
          onClick={() => setFilter('UNKNOWN')}
          style={{
            padding: '3px 9px',
            fontSize: '0.72rem',
            fontWeight: 600,
            borderRadius: '999px',
            border: filter === 'UNKNOWN' ? '1px solid #F59E0B' : '1px solid rgba(255,255,255,0.08)',
            background: filter === 'UNKNOWN' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255,255,255,0.02)',
            color: filter === 'UNKNOWN' ? '#FCD34D' : '#94A3B8',
            cursor: 'pointer',
          }}
        >
          Unknown ({countUnknown})
        </button>
      </div>

      {/* Findings List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {filteredFindings.map((finding, idx) => {
          const badge = getBadgeStyle(finding.category);
          return (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '8px',
                padding: '0.75rem 0.9rem',
                transition: 'border-color 0.15s',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.35rem',
                }}
              >
                <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#F8FAFC' }}>
                  {finding.title}
                </span>
                <span
                  style={{
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    padding: '2px 7px',
                    borderRadius: '999px',
                    background: badge.bg,
                    color: badge.text,
                    border: `1px solid ${badge.border}`,
                    letterSpacing: '0.04em',
                  }}
                  title={badge.label}
                >
                  {finding.category}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: '#94A3B8', lineHeight: 1.4, margin: '0 0 0.45rem 0' }}>
                {finding.detail}
              </p>
              {finding.evidence_ids.length > 0 && (
                <div style={{ display: 'flex', gap: '5px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.68rem', color: '#64748B' }}>Evidence:</span>
                  {finding.evidence_ids.map((id) => (
                    <span
                      key={id}
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '0.65rem',
                        background: 'rgba(6, 182, 212, 0.1)',
                        color: '#67E8F9',
                        padding: '1px 5px',
                        borderRadius: '4px',
                        border: '1px solid rgba(6, 182, 212, 0.25)',
                      }}
                    >
                      {id}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
