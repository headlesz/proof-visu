import React from 'react';
import {
  Box, Typography, List, ListItemButton, ListItemText, ListItemIcon, Chip, Paper,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import { ProofState } from '../types';

interface Props {
  proofState: ProofState | null;
  selectedGoal: string | null;
  onSelectGoal: (goalId: string) => void;
}

export default function GoalsList({ proofState, selectedGoal, onSelectGoal }: Props) {
  if (!proofState || !proofState.main_goal) {
    return (
      <Paper
        elevation={0}
        sx={{ flex: 1, p: 2, borderRadius: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          Enter a formula and click "Set Goal" to begin.
        </Typography>
      </Paper>
    );
  }

  const goals = Object.values(proofState.goals);
  const openGoals = goals.filter(g => !g.is_proven);
  const provenGoals = goals.filter(g => g.is_proven);

  return (
    <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
      <Box sx={{ px: 2, py: 1, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Typography variant="subtitle2" sx={{ color: 'text.secondary', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Goals
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
          <Chip label={`${openGoals.length} open`} size="small" color="warning" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
          <Chip label={`${provenGoals.length} proven`} size="small" color="success" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
        </Box>
      </Box>

      {proofState.premises.length > 0 && (
        <Box sx={{ px: 2, py: 1, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', textTransform: 'uppercase' }}>
            Premises
          </Typography>
          {proofState.premises.map((p, i) => (
            <Typography key={i} variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', mt: 0.25, color: '#81d4fa' }}>
              {p}
            </Typography>
          ))}
        </Box>
      )}

      <List dense sx={{ py: 0 }}>
        {goals.map(goal => (
          <ListItemButton
            key={goal.id}
            selected={selectedGoal === goal.id}
            onClick={() => !goal.is_proven && onSelectGoal(goal.id)}
            disabled={goal.is_proven}
            sx={{
              px: 2, py: 0.75,
              borderLeft: selectedGoal === goal.id ? '3px solid' : '3px solid transparent',
              borderLeftColor: selectedGoal === goal.id ? 'primary.main' : 'transparent',
              '&.Mui-selected': {
                backgroundColor: 'rgba(124,77,255,0.1)',
              },
              opacity: goal.is_proven ? 0.5 : 1,
            }}
          >
            <ListItemIcon sx={{ minWidth: 28 }}>
              {goal.is_proven
                ? <CheckCircleIcon sx={{ fontSize: 16, color: '#4caf50' }} />
                : <RadioButtonUncheckedIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              }
            </ListItemIcon>
            <ListItemText
              primary={
                <Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                    {goal.id} {goal.label && `- ${goal.label}`}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: '"JetBrains Mono", monospace',
                      fontSize: '0.8rem',
                      wordBreak: 'break-all',
                      color: goal.is_proven ? '#4caf50' : 'text.primary',
                    }}
                  >
                    {goal.formula}
                  </Typography>
                  {goal.rule_applied && (
                    <Chip
                      label={goal.rule_applied}
                      size="small"
                      sx={{ fontSize: '0.6rem', height: 16, mt: 0.25 }}
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Box>
              }
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}
