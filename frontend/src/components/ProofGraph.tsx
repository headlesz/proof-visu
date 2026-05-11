import React, { useRef, useEffect, useCallback } from 'react';
import { Box, Typography } from '@mui/material';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { GraphData } from '../types';

cytoscape.use(dagre);

interface Props {
  graphData: GraphData;
  selectedGoal: string | null;
  onSelectGoal: (goalId: string) => void;
}

const CYTOSCAPE_STYLE: any[] = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'text-wrap': 'wrap' as any,
      'text-max-width': '180px',
      'font-size': '11px',
      'font-family': '"JetBrains Mono", monospace',
      'color': '#e0e0e0',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#2d333b',
      'border-width': 2,
      'border-color': '#444c56',
      'shape': 'roundrectangle',
      'width': 'label',
      'height': 'label',
      'padding': '12px',
    },
  },
  {
    selector: 'node.open',
    style: {
      'border-color': '#f0883e',
      'background-color': '#2d1f0e',
    },
  },
  {
    selector: 'node.proven',
    style: {
      'border-color': '#3fb950',
      'background-color': '#0e2d1a',
      'color': '#7ee787',
    },
  },
  {
    selector: 'node.main',
    style: {
      'border-width': 3,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#7c4dff',
      'border-width': 3,
      'background-color': '#1a1040',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#444c56',
      'target-arrow-color': '#444c56',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': '9px',
      'font-family': '"JetBrains Mono", monospace',
      'color': '#768390',
      'text-rotation': 'autorotate',
    },
  },
];

export default function ProofGraph({ graphData, selectedGoal, onSelectGoal }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const onSelectGoalRef = useRef(onSelectGoal);
  onSelectGoalRef.current = onSelectGoal;

  // Initialize Cytoscape once and never destroy it during the component lifecycle
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      style: CYTOSCAPE_STYLE,
      layout: { name: 'preset' },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
    });

    cy.on('tap', 'node', (evt: any) => {
      const nodeId = evt.target.id();
      const nodeData = evt.target.data();
      if (!nodeData.is_proven) {
        onSelectGoalRef.current(nodeId);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, []);

  // Track previous graphData to avoid unnecessary rebuilds
  const prevGraphDataRef = useRef<GraphData | null>(null);

  // Update elements and selection when graphData or selectedGoal changes
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    // Only rebuild graph when graphData actually changes
    if (prevGraphDataRef.current !== graphData) {
      prevGraphDataRef.current = graphData;

      cy.elements().remove();

      if (graphData.nodes.length === 0) return;

      cy.add([...graphData.nodes, ...graphData.edges]);
      cy.layout({
        name: 'dagre',
        rankDir: 'TB',
        spacingFactor: 1.5,
        nodeSep: 50,
        rankSep: 80,
      } as any).run();
      cy.fit(undefined, 30);
    }

    // Always apply selection
    cy.elements().unselect();
    if (selectedGoal) {
      const node = cy.getElementById(selectedGoal);
      if (node.length > 0) {
        node.select();
      }
    }
  }, [graphData, selectedGoal]);

  const isEmpty = graphData.nodes.length === 0;

  return (
    <Box sx={{ height: '100%', width: '100%', position: 'relative', bgcolor: '#0d1117' }}>
      {/* Cytoscape container — always mounted so React never touches its children */}
      <Box
        ref={containerRef}
        sx={{
          height: '100%',
          width: '100%',
          visibility: isEmpty ? 'hidden' : 'visible',
        }}
      />
      {/* Placeholder overlay when empty */}
      {isEmpty && (
        <Box
          sx={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Proof graph will appear here after setting a goal.
          </Typography>
        </Box>
      )}
    </Box>
  );
}
