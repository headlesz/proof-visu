import React from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { ProofStep } from '../types';
import { RADII } from '../theme/radii';
import { COLORS } from '../theme/colors';

interface Props {
  steps: ProofStep[];
}

const RULE_COLORS: Record<string, string> = {
  assumption: COLORS.mint,
  contradiction: COLORS.blush,
  and_intro: COLORS.lavender,
  and_elim_left: COLORS.lavender,
  and_elim_right: COLORS.lavender,
  or_intro_left: COLORS.mint,
  or_intro_right: COLORS.mint,
  or_elim: COLORS.mint,
  implies_intro: COLORS.sky,
  implies_elim: COLORS.sky,
  not_intro: COLORS.butter,
  not_elim: COLORS.butter,
  iff_intro: COLORS.lavender,
  forall_intro: COLORS.mint,
  forall_elim: COLORS.mint,
  exists_intro: COLORS.mint,
  exists_elim: COLORS.mint,
  intersect_intro: COLORS.sky,
  intersect_elim: COLORS.sky,
  union_intro_left: COLORS.blush,
  union_intro_right: COLORS.blush,
  union_elim: COLORS.blush,
  complement_intro: COLORS.butter,
  complement_elim: COLORS.butter,
  not_complement_intro: COLORS.butter,
  not_complement_elim: COLORS.butter,
  not_element_intro: COLORS.butter,
  emptyset_elim: COLORS.blush,
  subset_intro: COLORS.sky,
  equality_intro: COLORS.lavender,
  induction: COLORS.mint,
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
          border: `1px dashed ${COLORS.lineStrong}`,
          bgcolor: 'rgba(255,255,255,0.03)',
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
        border: `1px solid ${COLORS.line}`,
        background: 'linear-gradient(145deg, rgba(14,14,14,0.76), rgba(7,7,7,0.64))',
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
            borderLeft: `3px solid ${RULE_COLORS[step.rule] || COLORS.muted}`,
            bgcolor: 'rgba(255,255,255,0.045)',
            borderColor: COLORS.line,
            animation: `fade-rise 380ms cubic-bezier(0.16, 1, 0.3, 1) ${Math.min(index * 18, 220)}ms both`,
            '&:hover': {
              transform: 'translateY(-1px)',
              bgcolor: 'rgba(255,255,255,0.07)',
              borderColor: COLORS.lineStrong,
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
                color: COLORS.black,
                bgcolor: RULE_COLORS[step.rule] || COLORS.muted,
              }}
            />
            {step.formula && (
              <Typography
                variant="body2"
                sx={{
                  fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                  fontSize: '0.74rem',
                  wordBreak: 'break-word',
                  color: 'text.primary',
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
