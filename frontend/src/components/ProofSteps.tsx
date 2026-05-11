import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { ProofStep } from '../types';

interface Props {
  steps: ProofStep[];
}

const RULE_COLORS: Record<string, string> = {
  assumption: '#4caf50',
  contradiction: '#f44336',
  and_intro: '#7c4dff',
  and_elim_left: '#7c4dff',
  and_elim_right: '#7c4dff',
  or_intro_left: '#ff9100',
  or_intro_right: '#ff9100',
  or_elim: '#ff9100',
  implies_intro: '#00e5ff',
  implies_elim: '#00e5ff',
  not_intro: '#e91e63',
  not_elim: '#e91e63',
  iff_intro: '#9c27b0',
  forall_intro: '#00bcd4',
  forall_elim: '#00bcd4',
  exists_intro: '#009688',
  exists_elim: '#009688',
  intersect_intro: '#ff5722',
  intersect_elim: '#ff5722',
  union_intro_left: '#795548',
  union_intro_right: '#795548',
  union_elim: '#795548',
  subset_intro: '#607d8b',
  equality_intro: '#ffc107',
  induction: '#69f0ae',
};

export default function ProofSteps({ steps }: Props) {
  if (steps.length === 0) {
    return (
      <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Proof steps will appear here as you apply rules.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto', p: 1.5 }}>
      <Typography variant="subtitle2" sx={{ color: 'text.secondary', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: 1, mb: 1 }}>
        Proof Steps
      </Typography>
      {steps.map((step, index) => (
        <Paper
          key={step.id}
          elevation={0}
          sx={{
            px: 1.5, py: 0.75, mb: 0.5,
            borderLeft: `3px solid ${RULE_COLORS[step.rule] || '#666'}`,
            bgcolor: 'rgba(255,255,255,0.02)',
            '&:hover': { bgcolor: 'rgba(255,255,255,0.04)' },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.65rem', minWidth: 20 }}>
              {index + 1}.
            </Typography>
            <Typography variant="caption" sx={{
              color: RULE_COLORS[step.rule] || '#aaa',
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '0.7rem',
              fontWeight: 600,
            }}>
              [{step.rule.replace(/_/g, ' ')}]
            </Typography>
            {step.formula && (
              <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem' }}>
                {step.formula}
              </Typography>
            )}
          </Box>
          {step.note && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem', ml: 3.5, display: 'block' }}>
              {step.note}
            </Typography>
          )}
        </Paper>
      ))}
    </Box>
  );
}
