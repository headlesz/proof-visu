import React, { useRef, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { GraphData } from '../types';
import { RADII } from '../theme/radii';
import { COLORS } from '../theme/colors';

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
      color: COLORS.white,
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': COLORS.ink,
      'border-width': 1.8,
      'border-color': 'rgba(255,255,255,0.55)',
      shape: 'roundrectangle',
      width: 'label',
      height: 'label',
      padding: '13px',
      'text-background-color': 'rgba(0,0,0,0.52)',
      'text-background-opacity': 0.2,
      'text-background-padding': '2px',
    },
  },
  {
    selector: 'node.open',
    style: {
      'border-color': COLORS.butter,
      'background-color': '#1b1a14',
      color: COLORS.butter,
    },
  },
  {
    selector: 'node.proven',
    style: {
      'border-color': COLORS.mint,
      'background-color': '#121d18',
      color: COLORS.mint,
    },
  },
  {
    selector: 'node.main',
    style: {
      'border-width': 2.6,
      'border-color': COLORS.lavender,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#ffb87a',
      'border-width': 3,
      'overlay-opacity': 0,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 1.9,
      'line-color': 'rgba(255,255,255,0.42)',
      'target-arrow-color': 'rgba(255,255,255,0.42)',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': '11px',
      'font-weight': 700,
      'font-family': '"DM Mono", "JetBrains Mono", monospace',
      color: COLORS.white,
      'text-outline-width': 2,
      'text-outline-color': COLORS.black,
      'text-rotation': 'autorotate',
      'text-background-color': COLORS.black,
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
        border: `1px solid ${COLORS.line}`,
        background: 'linear-gradient(145deg, rgba(18,18,18,0.96), rgba(7,7,7,0.92))',
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
