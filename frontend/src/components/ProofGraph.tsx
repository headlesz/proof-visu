import React, { useRef, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { GraphData } from '../types';
import { RADII } from '../theme/radii';

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
      label: 'data(label)',
      'text-wrap': 'wrap' as any,
      'text-max-width': '188px',
      'font-size': '10.8px',
      'font-family': '"DM Mono", "JetBrains Mono", monospace',
      color: '#f4f1e8',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#18323b',
      'border-width': 1.8,
      'border-color': 'rgba(183,200,202,0.65)',
      shape: 'roundrectangle',
      width: 'label',
      height: 'label',
      padding: '13px',
      'text-background-color': 'rgba(16,32,39,0.56)',
      'text-background-opacity': 0.2,
      'text-background-padding': '2px',
    },
  },
  {
    selector: 'node.open',
    style: {
      'border-color': '#f4a261',
      'background-color': '#30251c',
      color: '#f6d4b4',
    },
  },
  {
    selector: 'node.proven',
    style: {
      'border-color': '#7dd3a7',
      'background-color': '#173128',
      color: '#bce9d1',
    },
  },
  {
    selector: 'node.main',
    style: {
      'border-width': 2.6,
      'border-color': '#2a9d8f',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#2a9d8f',
      'border-width': 3,
      'background-color': '#123337',
      'overlay-opacity': 0,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 1.9,
      'line-color': 'rgba(167,187,192,0.58)',
      'target-arrow-color': 'rgba(167,187,192,0.58)',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': '11px',
      'font-weight': 700,
      'font-family': '"DM Mono", "JetBrains Mono", monospace',
      color: '#f4f1e8',
      'text-outline-width': 2,
      'text-outline-color': '#081116',
      'text-rotation': 'autorotate',
      'text-background-color': '#081116',
      'text-background-opacity': 0.85,
      'text-background-padding': '4px',
    },
  },
];

export default function ProofGraph({ graphData, selectedGoal, onSelectGoal }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const onSelectGoalRef = useRef(onSelectGoal);
  onSelectGoalRef.current = onSelectGoal;

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
      wheelSensitivity: 0.24,
      motionBlur: true,
      textureOnViewport: true,
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

  const prevGraphDataRef = useRef<GraphData | null>(null);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    if (prevGraphDataRef.current !== graphData) {
      prevGraphDataRef.current = graphData;

      cy.elements().remove();

      if (graphData.nodes.length === 0) return;

      cy.add([...graphData.nodes, ...graphData.edges]);
      cy.layout({
        name: 'dagre',
        rankDir: 'TB',
        spacingFactor: 1.42,
        nodeSep: 46,
        rankSep: 84,
        animate: false,
      } as any).run();
      cy.fit(undefined, 36);
    }

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
    <Box
      sx={{
        height: '100%',
        width: '100%',
        position: 'relative',
        borderRadius: RADII.panel,
        overflow: 'hidden',
        border: '1px solid rgba(183,200,202,0.2)',
        background:
          'linear-gradient(145deg, rgba(14,28,33,0.95), rgba(16,32,39,0.88))',
      }}
    >
      <Box
        ref={containerRef}
        sx={{
          height: '100%',
          width: '100%',
          visibility: isEmpty ? 'hidden' : 'visible',
          animation: isEmpty ? 'none' : 'fade-rise 500ms cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      />
      {isEmpty && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
            p: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', maxWidth: 380 }}>
            Your proof graph will materialize here as soon as you set a goal and start applying rules.
          </Typography>
        </Box>
      )}
    </Box>
  );
}
