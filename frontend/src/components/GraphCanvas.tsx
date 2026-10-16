import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { GraphTopology } from '../types';

interface GraphCanvasProps {
  topology: GraphTopology | null;
  highlightedPath?: string[];
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ topology, highlightedPath }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !topology) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Nodes
    topology.nodes.forEach((n) => {
      const name = n.properties.name || n.properties.title || n.properties.id || n.id;
      const isFailing = n.properties.health === 'FAILING' || n.properties.status === 'OUTAGE';
      const isHighlighted = highlightedPath?.some((p) => p.includes(n.id) || p.includes(name));
      
      elements.push({
        group: 'nodes',
        data: {
          id: n.id,
          label: name,
          type: n.label,
          health: n.properties.health || 'NORMAL',
          isFailing: isFailing ? 'true' : 'false',
          isHighlighted: isHighlighted ? 'true' : 'false',
        },
      });
    });

    // Edges
    topology.edges.forEach((e, idx) => {
      elements.push({
        group: 'edges',
        data: {
          id: `edge-${idx}`,
          source: e.source,
          target: e.target,
          rel: e.relationship,
        },
      });
    });

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#F1F5F9',
            'font-size': '10px',
            'font-family': 'Plus Jakarta Sans, sans-serif',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': '#3B82F6',
            'width': 30,
            'height': 30,
            'border-width': 2,
            'border-color': 'rgba(255,255,255,0.2)',
          },
        },
        {
          selector: 'node[type = "Incident"]',
          style: {
            'background-color': '#EF4444',
            'width': 38,
            'height': 38,
            'border-color': '#FCA5A5',
            'border-width': 3,
          },
        },
        {
          selector: 'node[type = "Service"]',
          style: {
            'background-color': '#06B6D4',
            'width': 32,
            'height': 32,
          },
        },
        {
          selector: 'node[isFailing = "true"]',
          style: {
            'background-color': '#DC2626',
            'border-color': '#F87171',
            'border-width': 4,
          },
        },
        {
          selector: 'node[type = "Deployment"]',
          style: {
            'background-color': '#F59E0B',
            'shape': 'round-rectangle',
            'width': 28,
            'height': 28,
          },
        },
        {
          selector: 'node[type = "Vulnerability"]',
          style: {
            'background-color': '#A855F7',
            'shape': 'diamond',
            'width': 32,
            'height': 32,
          },
        },
        {
          selector: 'node[type = "Alert"]',
          style: {
            'background-color': '#EC4899',
            'width': 24,
            'height': 24,
          },
        },
        {
          selector: 'node[type = "Evidence"]',
          style: {
            'background-color': '#10B981',
            'width': 22,
            'height': 22,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': 'rgba(255, 255, 255, 0.16)',
            'target-arrow-color': 'rgba(255, 255, 255, 0.3)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(rel)',
            'font-size': '8px',
            'color': '#64748B',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
          },
        },
        {
          selector: 'edge[rel = "DEPENDS_ON"]',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'width': 2.5,
          },
        },
        {
          selector: 'edge[rel = "DEPLOYED_IN"]',
          style: {
            'line-color': '#F59E0B',
            'target-arrow-color': '#F59E0B',
            'line-style': 'dashed',
          },
        },
        {
          selector: 'edge[rel = "HAS_VULNERABILITY"]',
          style: {
            'line-color': '#A855F7',
            'target-arrow-color': '#A855F7',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        padding: 40,
        nodeRepulsion: () => 6500,
        idealEdgeLength: () => 80,
      },
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [topology]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '380px' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%', background: '#090D15', borderRadius: '8px' }} />
      <div style={{
        position: 'absolute',
        bottom: '12px',
        left: '12px',
        background: 'rgba(14, 19, 31, 0.85)',
        border: '1px solid rgba(255,255,255,0.1)',
        backdropFilter: 'blur(8px)',
        borderRadius: '6px',
        padding: '6px 10px',
        fontSize: '0.7rem',
        display: 'flex',
        gap: '12px',
        color: '#94A3B8'
      }}>
        <span><b style={{ color: '#EF4444' }}>●</b> Incident</span>
        <span><b style={{ color: '#06B6D4' }}>●</b> Service</span>
        <span><b style={{ color: '#F59E0B' }}>■</b> Deployment</span>
        <span><b style={{ color: '#A855F7' }}>◆</b> Vulnerability</span>
        <span><b style={{ color: '#10B981' }}>●</b> Evidence</span>
      </div>
    </div>
  );
};
