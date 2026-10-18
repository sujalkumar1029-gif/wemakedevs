import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { GraphTopology } from '../types';

interface GraphCanvasProps {
  topology: GraphTopology | null;
  highlightedPath?: string[];
  activeStep?: number | null;
  onNodeSelect?: (nodeData: any) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  topology,
  highlightedPath,
  activeStep,
  onNodeSelect,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [layoutMode, setLayoutMode] = useState<'cose' | 'breadthfirst'>('cose');
  const [filterType, setFilterType] = useState<string>('ALL');

  // Initialize and update elements
  useEffect(() => {
    if (!containerRef.current || !topology) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Filter nodes based on filterType
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
          health: n.properties.health || 'HEALTHY',
          criticality: n.properties.criticality || 'NORMAL',
          isFailing: isFailing ? 'true' : 'false',
          isHighlighted: isHighlighted ? 'true' : 'false',
          rawProperties: n.properties,
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
      try {
        cyRef.current.stop();
        cyRef.current.destroy();
      } catch {
        // ignore
      }
      cyRef.current = null;
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#CBD5E1',
            'font-size': '10px',
            'font-family': 'Plus Jakarta Sans, sans-serif',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': '#3B82F6',
            'width': 28,
            'height': 28,
            'border-width': 2,
            'border-color': 'rgba(255, 255, 255, 0.15)',
            'transition-property': 'background-color, border-color, width, height, opacity',
            'transition-duration': 0.25,
          },
        },
        {
          selector: 'node[type = "Incident"]',
          style: {
            'background-color': '#EF4444',
            'border-color': '#FCA5A5',
            'border-width': 3,
            'width': 36,
            'height': 36,
          },
        },
        {
          selector: 'node[type = "Service"]',
          style: {
            'background-color': '#06B6D4',
            'border-color': 'rgba(6, 182, 212, 0.4)',
            'width': 30,
            'height': 30,
          },
        },
        {
          selector: 'node[isFailing = "true"]',
          style: {
            'background-color': '#DC2626',
            'border-color': '#F87171',
            'border-width': 4,
            'width': 34,
            'height': 34,
            'color': '#FCA5A5',
          },
        },
        {
          selector: 'node[type = "Deployment"]',
          style: {
            'background-color': '#F59E0B',
            'shape': 'round-rectangle',
            'width': 26,
            'height': 26,
          },
        },
        {
          selector: 'node[type = "Vulnerability"]',
          style: {
            'background-color': '#8B5CF6',
            'shape': 'diamond',
            'width': 28,
            'height': 28,
          },
        },
        {
          selector: 'node[type = "Alert"]',
          style: {
            'background-color': '#EC4899',
            'width': 22,
            'height': 22,
          },
        },
        {
          selector: 'node[type = "Evidence"]',
          style: {
            'background-color': '#10B981',
            'width': 20,
            'height': 20,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#FFFFFF',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': 'rgba(255, 255, 255, 0.12)',
            'target-arrow-color': 'rgba(255, 255, 255, 0.25)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(rel)',
            'font-size': '8px',
            'color': '#64748B',
            'text-rotation': 'autorotate',
            'text-margin-y': -6,
            'transition-property': 'opacity, width, line-color',
            'transition-duration': 0.25,
          },
        },
        {
          selector: 'edge[rel = "DEPENDS_ON"]',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'width': 2.2,
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
            'line-color': '#8B5CF6',
            'target-arrow-color': '#8B5CF6',
          },
        },
      ],
      layout: {
        name: layoutMode,
        animate: false,
        padding: 35,
        ...(layoutMode === 'cose'
          ? { nodeRepulsion: () => 7000, idealEdgeLength: () => 75 }
          : { directed: true, spacingFactor: 1.25 }),
      },
    });

    // Handle node selection
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const data = node.data();
      setSelectedNode(data);
      if (onNodeSelect) onNodeSelect(data);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        if (onNodeSelect) onNodeSelect(null);
      }
    });

    cyRef.current = cy;

    return () => {
      try {
        cy.stop();
        cy.removeAllListeners();
        cy.destroy();
      } catch {
        // ignore
      }
      cyRef.current = null;
    };
  }, [topology, layoutMode]);

  // Apply node filters when filterType changes
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    if (filterType === 'ALL') {
      cy.elements().style('opacity', 1);
    } else {
      cy.nodes().forEach((n) => {
        if (n.data('type') === filterType) {
          n.style('opacity', 1);
        } else {
          n.style('opacity', 0.12);
        }
      });
      cy.edges().style('opacity', 0.15);
    }
  }, [filterType]);

  // Handle activeStep highlighting during Step-by-Step Demo Walkthrough
  useEffect(() => {
    if (!cyRef.current || activeStep === null || activeStep === undefined) return;
    const cy = cyRef.current;

    cy.elements().style('opacity', 0.2);

    if (activeStep === 1) {
      // Step 1: get_incident_context -> Highlight Incident and Alerts
      const targets = cy.nodes('[type = "Incident"], [type = "Alert"]');
      targets.style('opacity', 1);
      targets.connectedEdges().style('opacity', 0.8);
      if (targets.length > 0) cy.center(targets);
    } else if (activeStep === 2) {
      // Step 2: trace_candidate_causes -> Highlight primary service & candidate causes
      const targets = cy.nodes('[type = "Service"][isFailing = "true"], [type = "Deployment"], [type = "Vulnerability"]');
      targets.style('opacity', 1);
      targets.connectedEdges().style('opacity', 0.8);
      if (targets.length > 0) cy.center(targets);
    } else if (activeStep === 3) {
      // Step 3: get_deployment_history
      const targets = cy.nodes('[type = "Deployment"]');
      targets.style('opacity', 1);
      targets.connectedEdges().style('opacity', 0.8);
    } else if (activeStep === 4) {
      // Step 4: get_evidence_chain -> Highlight Evidence nodes
      const targets = cy.nodes('[type = "Evidence"]');
      targets.style('opacity', 1);
      targets.connectedEdges().style('opacity', 0.8);
    } else if (activeStep === 5) {
      // Step 5: get_blast_radius -> Highlight reverse DEPENDS_ON chain
      const targets = cy.nodes('[type = "Service"]');
      targets.style('opacity', 1);
      cy.edges('[rel = "DEPENDS_ON"]').style('opacity', 1);
      if (targets.length > 0) cy.center(targets);
    } else if (activeStep === 6) {
      // Step 6: get_service_owner
      const targets = cy.nodes('[type = "Service"][isFailing = "true"]');
      targets.style('opacity', 1);
    } else if (activeStep === 7) {
      // Step 7: propose_response -> Full verified path
      cy.elements().style('opacity', 1);
    }
  }, [activeStep]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 30);

  const toggleLayout = () => {
    const nextLayout = layoutMode === 'cose' ? 'breadthfirst' : 'cose';
    setLayoutMode(nextLayout);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '380px' }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '380px',
          background: 'rgba(5, 8, 15, 0.95)',
          borderRadius: '8px',
        }}
      />

      {/* Top Left: Filter Chips & Layout Toggle */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          display: 'flex',
          gap: '6px',
          flexWrap: 'wrap',
          zIndex: 10,
        }}
      >
        <button
          onClick={toggleLayout}
          style={{
            padding: '3px 8px',
            fontSize: '0.68rem',
            fontWeight: 700,
            borderRadius: '4px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            color: '#93C5FD',
            cursor: 'pointer',
          }}
          title="Toggle Layout (Force-Directed vs Hierarchical)"
        >
          {layoutMode === 'cose' ? '☊ Tree Layout' : '🕸️ Force Layout'}
        </button>

        <div style={{ display: 'flex', gap: '3px', background: 'rgba(15, 23, 42, 0.85)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border)' }}>
          {['ALL', 'Service', 'Deployment', 'Alert', 'Evidence'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              style={{
                padding: '2px 6px',
                fontSize: '0.65rem',
                fontWeight: 600,
                borderRadius: '3px',
                border: 'none',
                background: filterType === type ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                color: filterType === type ? '#F8FAFC' : '#94A3B8',
                cursor: 'pointer',
              }}
            >
              {type === 'ALL' ? 'All' : type}
            </button>
          ))}
        </div>
      </div>

      {/* Floating Canvas Zoom Controls */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          zIndex: 10,
        }}
      >
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          style={{
            width: '28px',
            height: '28px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '6px',
            color: '#CBD5E1',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          style={{
            width: '28px',
            height: '28px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '6px',
            color: '#CBD5E1',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          −
        </button>
        <button
          onClick={handleFit}
          title="Center Graph"
          style={{
            width: '28px',
            height: '28px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '6px',
            color: '#CBD5E1',
            cursor: 'pointer',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          ⤢
        </button>
      </div>

      {/* Selected Node Inspector Drawer */}
      {selectedNode && (
        <div
          style={{
            position: 'absolute',
            bottom: '40px',
            left: '12px',
            maxWidth: '280px',
            background: 'rgba(15, 23, 42, 0.94)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            backdropFilter: 'blur(12px)',
            borderRadius: '8px',
            padding: '10px 12px',
            zIndex: 10,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: '#06B6D4', fontWeight: 700, textTransform: 'uppercase' }}>
              {selectedNode.type}
            </span>
            <button
              onClick={() => setSelectedNode(null)}
              style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: '13px' }}
            >
              ×
            </button>
          </div>
          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#F8FAFC', marginBottom: '6px' }}>
            {selectedNode.label}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {selectedNode.health && (
              <div>
                Health:{' '}
                <span style={{ color: selectedNode.health === 'FAILING' ? '#EF4444' : '#10B981', fontWeight: 600 }}>
                  {selectedNode.health}
                </span>
              </div>
            )}
            {selectedNode.criticality && <div>Tier: {selectedNode.criticality}</div>}
            {selectedNode.rawProperties?.version && <div>Version: {selectedNode.rawProperties.version}</div>}
            {selectedNode.rawProperties?.commit_sha && <div>Commit: {selectedNode.rawProperties.commit_sha}</div>}
            {selectedNode.rawProperties?.observed_value && <div>Value: {selectedNode.rawProperties.observed_value}</div>}
          </div>
        </div>
      )}

      {/* Minimal Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '12px',
          background: 'rgba(10, 15, 26, 0.88)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(8px)',
          borderRadius: '6px',
          padding: '5px 10px',
          fontSize: '0.68rem',
          display: 'flex',
          gap: '10px',
          color: '#94A3B8',
          zIndex: 5,
        }}
      >
        <span><b style={{ color: '#EF4444' }}>●</b> Incident</span>
        <span><b style={{ color: '#06B6D4' }}>●</b> Service</span>
        <span><b style={{ color: '#F59E0B' }}>■</b> Deployment</span>
        <span><b style={{ color: '#8B5CF6' }}>◆</b> CVE</span>
        <span><b style={{ color: '#EC4899' }}>●</b> Alert</span>
        <span><b style={{ color: '#10B981' }}>●</b> Evidence</span>
      </div>
    </div>
  );
};
