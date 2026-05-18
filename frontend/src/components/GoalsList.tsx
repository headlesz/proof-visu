import React from 'react';
import {
  Box, Typography, List, ListItemButton, ListItemText, ListItemIcon, Chip, Paper, Tooltip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import { ProofState } from '../types';
import { RADII } from '../theme/radii';

interface Props {
  proofState: ProofState | null;
  selectedGoal: string | null;
  onSelectGoal: (goalId: string) => void;
  onRemovePremise: (premiseIndex: number) => void;
}

export default function GoalsList({ proofState, selectedGoal, onSelectGoal, onRemovePremise }: Props) {
  if (!proofState || !proofState.main_goal) {
    return (
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          p: 2,
          borderRadius: RADII.panel,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'transparent',
          border: 'none',
          boxShadow: 'none',
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          Start by entering a formula, then set a goal.
        </Typography>
      </Paper>
    );
  }

  const goals = Object.values(proofState.goals);
  const openGoals = goals.filter(g => !g.is_proven);
  const provenGoals = goals.filter(g => g.is_proven);

  return (
    <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0, borderBottom: '1px solid rgba(183,200,202,0.15)' }}>
      <Box sx={{ px: 1.35, py: 1.05, borderBottom: '1px solid rgba(183,200,202,0.15)' }}>
        <Typography
          variant="subtitle2"
          sx={{
            color: 'text.secondary',
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: 1.1,
          }}
        >
          Goals
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.7, mt: 0.7 }}>
          <Chip
            label={`${openGoals.length} open`}
            size="small"
            sx={{
              fontSize: '0.67rem',
              height: 22,
              color: '#0f1f24',
              bgcolor: 'warning.main',
              border: '1px solid rgba(246,193,119,0.6)',
            }}
          />
          <Chip
            label={`${provenGoals.length} proven`}
            size="small"
            sx={{
              fontSize: '0.67rem',
              height: 22,
              color: '#0f1f24',
              bgcolor: 'success.main',
              border: '1px solid rgba(125,211,167,0.62)',
            }}
          />
        </Box>
      </Box>

      {proofState.premises.length > 0 && (
        <Box sx={{ px: 1.35, py: 0.9, borderBottom: '1px dashed rgba(183,200,202,0.18)' }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: 0.8 }}>
            Premises
          </Typography>
          {proofState.premises.map((p, i) => (
            <Tooltip key={`${p}-${i}`} title="Remove premise" placement="right" arrow>
              <Typography
                component="button"
                type="button"
                variant="body2"
                onClick={() => onRemovePremise(i)}
                sx={{
                  display: 'block',
                  width: '100%',
                  border: '1px solid transparent',
                  borderRadius: RADII.control,
                  mt: 0.35,
                  px: 0.45,
                  py: 0.32,
                  bgcolor: 'transparent',
                  fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                  fontSize: '0.73rem',
                  lineHeight: 1.45,
                  textAlign: 'left',
                  wordBreak: 'break-word',
                  color: 'secondary.main',
                  opacity: 0.95,
                  cursor: 'pointer',
                  transition: 'background-color 160ms ease, border-color 160ms ease, color 160ms ease',
                  '&:hover': {
                    color: 'error.main',
                    bgcolor: 'rgba(239,125,104,0.08)',
                    borderColor: 'rgba(239,125,104,0.3)',
                  },
                  '&:focus-visible': {
                    outline: 'none',
                    borderColor: 'rgba(239,125,104,0.72)',
                    boxShadow: '0 0 0 3px rgba(239,125,104,0.18)',
                  },
                }}
              >
                {p}
              </Typography>
            </Tooltip>
          ))}
        </Box>
      )}

      <List dense sx={{ py: 0.55 }}>
        {goals.map((goal, idx) => (
          <ListItemButton
            key={goal.id}
            selected={selectedGoal === goal.id}
            onClick={() => !goal.is_proven && onSelectGoal(goal.id)}
            disabled={goal.is_proven}
            sx={{
              mx: 0.7,
              mb: 0.52,
              borderRadius: RADII.control,
              px: 1.05,
              py: 0.7,
              border: '1px solid transparent',
              animation: `fade-rise 420ms cubic-bezier(0.16, 1, 0.3, 1) ${Math.min(idx * 22, 260)}ms both`,
              '&.Mui-selected': {
                bgcolor: 'rgba(42,157,143,0.14)',
                borderColor: 'rgba(42,157,143,0.4)',
              },
              '&:hover': {
                transform: 'translateY(-1px)',
                bgcolor: 'rgba(244,162,97,0.09)',
                borderColor: 'rgba(244,162,97,0.28)',
              },
              opacity: goal.is_proven ? 0.62 : 1,
              transition: 'transform 180ms ease, background-color 180ms ease, border-color 180ms ease, opacity 180ms ease',
            }}
          >
            <ListItemIcon sx={{ minWidth: 26 }}>
              {goal.is_proven
                ? <CheckCircleIcon sx={{ fontSize: 16, color: '#7dd3a7' }} />
                : <RadioButtonUncheckedIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              }
            </ListItemIcon>
            <ListItemText
              primary={(
                <Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.63rem' }}>
                    {goal.id} {goal.label && `- ${goal.label}`}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                      fontSize: '0.77rem',
                      wordBreak: 'break-word',
                      color: goal.is_proven ? '#7dd3a7' : 'text.primary',
                    }}
                  >
                    {goal.formula}
                  </Typography>
                  {goal.rule_applied && (
                    <Chip
                      label={goal.rule_applied.replace(/_/g, ' ')}
                      size="small"
                      sx={{
                        fontSize: '0.6rem',
                        height: 17,
                        mt: 0.35,
                        border: '1px solid rgba(125,211,167,0.45)',
                        color: '#7dd3a7',
                        bgcolor: 'rgba(125,211,167,0.08)',
                      }}
                      variant="outlined"
                    />
                  )}
                </Box>
              )}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}
