import React from 'react';
import type { Finding } from '../types';

interface FindingsPanelProps {
  findings: Finding[];
}

export const FindingsPanel: React.FC<FindingsPanelProps> = ({ findings }) => {
  const getBadgeStyle = (category: string) => {
    switch (category) {
      case 'OBSERVED':
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#6EE7B7', border: 'rgba(16, 185, 129, 0.3)' };
      case 'INFERRED':
        return { bg: 'rgba(168, 85, 247, 0.15)', text: '#D8B4FE', border: 'rgba(168, 85, 247, 0.3)' };
      case 'UNKNOWN':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#FCD34D', border: 'rgba(245, 158, 11, 0.3)' };
      default:
        return { bg: 'rgba(255, 255, 255, 0.1)', text: '#F1F5F9', border: 'rgba(255, 255, 255, 0.2)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {findings.map((finding, idx) => {
        const badge = getBadgeStyle(finding.category);
        return (
          <div
            key={idx}
            style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.07)',
              borderRadius: '8px',
              padding: '0.85rem',
              transition: 'border-color 0.2s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#F1F5F9' }}>{finding.title}</span>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: badge.bg,
                  color: badge.text,
                  border: `1px solid ${badge.border}`,
                  letterSpacing: '0.05em',
                }}
              >
                {finding.category}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8', lineHeight: 1.4, margin: '0 0 0.5rem 0' }}>
              {finding.detail}
            </p>
            {finding.evidence_ids.length > 0 && (
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.7rem', color: '#64748B' }}>Evidence:</span>
                {finding.evidence_ids.map((id) => (
                  <span
                    key={id}
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '0.68rem',
                      background: 'rgba(6, 182, 212, 0.12)',
                      color: '#06B6D4',
                      padding: '1px 6px',
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
  );
};
