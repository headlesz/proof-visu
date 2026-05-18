import React from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { ProofStep } from '../types';
import { RADII } from '../theme/radii';

interface Props {
  steps: ProofStep[];
}

const RULE_COLORS: Record<string, string> = {
  assumption: '#7dd3a7',
  contradiction: '#ef7d68',
  and_intro: '#f4a261',
  and_elim_left: '#f4a261',
  and_elim_right: '#f4a261',
  or_intro_left: '#66c7bc',
  or_intro_right: '#66c7bc',
  or_elim: '#66c7bc',
  implies_intro: '#a9c0d0',
  implies_elim: '#a9c0d0',
  not_intro: '#eab676',
  not_elim: '#eab676',
  iff_intro: '#d3ba8d',
  forall_intro: '#9fd5ce',
  forall_elim: '#9fd5ce',
  exists_intro: '#84c7ab',
  exists_elim: '#84c7ab',
  intersect_intro: '#f8b279',
  intersect_elim: '#f8b279',
  union_intro_left: '#eb9176',
  union_intro_right: '#eb9176',
  union_elim: '#eb9176',
  complement_intro: '#c9df8a',
  complement_elim: '#c9df8a',
  not_complement_intro: '#b7d77a',
  not_complement_elim: '#b7d77a',
  not_element_intro: '#d5c96a',
  emptyset_elim: '#d9a66d',
  subset_intro: '#b8c9cd',
  equality_intro: '#ffd28f',
  induction: '#8bd3a8',
};

export default function ProofSteps({ steps }: Props) {
  if (steps.length === 0) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: RADII.panel,
          border: '1px dashed rgba(183,200,202,0.24)',
          bgcolor: 'rgba(11,20,24,0.38)',
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', px: 2 }}>
          Proof steps will stream in here as you apply each inference rule.
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        height: '100%',
        overflow: 'auto',
        p: 1,
        borderRadius: RADII.panel,
        border: '1px solid rgba(183,200,202,0.2)',
        background: 'linear-gradient(145deg, rgba(11,20,24,0.58), rgba(16,32,39,0.55))',
      }}
    >
      <Typography
        variant="subtitle2"
        sx={{
          color: 'text.secondary',
          fontSize: '0.7rem',
          textTransform: 'uppercase',
          letterSpacing: 1.1,
          px: 0.35,
          mb: 0.75,
        }}
      >
        Proof Steps
      </Typography>

      {steps.map((step, index) => (
        <Paper
          key={step.id}
          elevation={0}
          sx={{
            px: 1.2,
            py: 0.72,
            mb: 0.52,
            borderRadius: RADII.control,
            borderLeft: `3px solid ${RULE_COLORS[step.rule] || '#a7bbc0'}`,
            bgcolor: 'rgba(14,28,33,0.68)',
            borderColor: 'rgba(183,200,202,0.18)',
            animation: `fade-rise 380ms cubic-bezier(0.16, 1, 0.3, 1) ${Math.min(index * 18, 220)}ms both`,
            '&:hover': {
              transform: 'translateY(-1px)',
              bgcolor: 'rgba(20,38,45,0.8)',
              borderColor: 'rgba(244,162,97,0.28)',
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8, flexWrap: 'wrap' }}>
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                fontSize: '0.64rem',
                minWidth: 22,
              }}
            >
              {index + 1}.
            </Typography>
            <Chip
              label={step.rule.replace(/_/g, ' ')}
              size="small"
              sx={{
                height: 19,
                fontSize: '0.6rem',
                fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                color: '#102027',
                bgcolor: RULE_COLORS[step.rule] || '#a7bbc0',
              }}
            />
            {step.formula && (
              <Typography
                variant="body2"
                sx={{
                  fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                  fontSize: '0.74rem',
                  wordBreak: 'break-word',
                  color: '#f4f1e8',
                }}
              >
                {step.formula}
              </Typography>
            )}
          </Box>
          {step.note && (
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontSize: '0.68rem',
                ml: 3.5,
                display: 'block',
                mt: 0.3,
              }}
            >
              {step.note}
            </Typography>
          )}
        </Paper>
      ))}
    </Box>
  );
}
