import React, { useState } from 'react';
import {
  Box, Typography, Button, Collapse, TextField, Paper, Chip, Tooltip,
} from '@mui/material';
import GavelIcon from '@mui/icons-material/Gavel';
import { RuleInfo } from '../types';
import { RADII } from '../theme/radii';

interface Props {
  rules: RuleInfo[];
  selectedGoal: string | null;
  onApplyRule: (ruleName: string, params?: any) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  propositional: '#f4a261',
  quantifier: '#66c7bc',
  set_theory: '#e76f51',
  induction: '#8bd3a8',
  general: '#a7bbc0',
};

export default function RulesPanel({ rules, selectedGoal, onApplyRule }: Props) {
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [paramInput, setParamInput] = useState('');

  if (!selectedGoal) {
    return (
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          p: 1.5,
          borderRadius: RADII.panel,
          bgcolor: 'transparent',
          border: 'none',
          boxShadow: 'none',
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', fontSize: '0.82rem' }}>
          Select an open goal to unlock rule actions.
        </Typography>
      </Paper>
    );
  }

  const grouped = rules.reduce<Record<string, RuleInfo[]>>((acc, r) => {
    (acc[r.category] = acc[r.category] || []).push(r);
    return acc;
  }, {});

  const handleApply = (rule: RuleInfo) => {
    const needsParam = ['forall_elim', 'exists_intro'].includes(rule.name);
    if (needsParam && expandedRule !== rule.name) {
      setExpandedRule(rule.name);
      setParamInput('');
    } else if (needsParam && paramInput.trim()) {
      onApplyRule(rule.name, { term: paramInput.trim() });
      setExpandedRule(null);
      setParamInput('');
    } else if (!needsParam) {
      onApplyRule(rule.name);
    }
  };

  return (
    <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
      <Box sx={{ px: 1.35, py: 1, borderBottom: '1px solid rgba(183,200,202,0.15)', display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          sx={{
            width: 24,
            height: 24,
            borderRadius: RADII.icon,
            display: 'grid',
            placeItems: 'center',
            bgcolor: 'rgba(42,157,143,0.18)',
            border: '1px solid rgba(42,157,143,0.45)',
          }}
        >
          <GavelIcon sx={{ fontSize: 14, color: 'secondary.main' }} />
        </Box>
        <Typography variant="subtitle2" sx={{ color: 'text.secondary', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Rules ({rules.length})
        </Typography>
      </Box>

      {rules.length === 0 ? (
        <Box sx={{ p: 1.35 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
            No applicable rules for this goal.
          </Typography>
        </Box>
      ) : (
        Object.entries(grouped).map(([category, catRules], categoryIndex) => (
          <Box key={category} sx={{ px: 1.05, pt: 0.75, pb: 0.3 }}>
            <Chip
              label={category.replace('_', ' ')}
              size="small"
              sx={{
                fontSize: '0.6rem',
                height: 18,
                mb: 0.6,
                color: CATEGORY_COLORS[category] || '#a7bbc0',
                borderColor: `${CATEGORY_COLORS[category] || '#a7bbc0'}88`,
                backgroundColor: `${CATEGORY_COLORS[category] || '#a7bbc0'}16`,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}
              variant="outlined"
            />

            {catRules.map((rule, index) => (
              <Box key={rule.name} sx={{ mb: 0.48 }}>
                <Tooltip title={rule.description} placement="right" arrow>
                  <Button
                    fullWidth
                    size="small"
                    variant={expandedRule === rule.name ? 'contained' : 'outlined'}
                    onClick={() => handleApply(rule)}
                    sx={{
                      justifyContent: 'flex-start',
                      fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                      fontSize: '0.73rem',
                      py: 0.62,
                      borderRadius: RADII.control,
                      textTransform: 'none',
                      borderColor: `${CATEGORY_COLORS[rule.category] || '#a7bbc0'}55`,
                      color: expandedRule === rule.name ? '#102027' : CATEGORY_COLORS[rule.category] || 'text.primary',
                      bgcolor: expandedRule === rule.name ? CATEGORY_COLORS[rule.category] || '#a7bbc0' : 'rgba(11,20,24,0.4)',
                      animation: `fade-rise 380ms cubic-bezier(0.16, 1, 0.3, 1) ${Math.min(220, (categoryIndex * 90) + (index * 16))}ms both`,
                      '&:hover': {
                        borderColor: `${CATEGORY_COLORS[rule.category] || '#a7bbc0'}bb`,
                        bgcolor: expandedRule === rule.name ? CATEGORY_COLORS[rule.category] || '#a7bbc0' : `${CATEGORY_COLORS[rule.category] || '#a7bbc0'}1A`,
                      },
                    }}
                  >
                    {rule.name.replace(/_/g, ' ')}
                  </Button>
                </Tooltip>
                <Collapse in={expandedRule === rule.name}>
                  <Box sx={{ px: 0.45, pt: 0.58, display: 'flex', gap: 0.45 }}>
                    <TextField
                      size="small"
                      placeholder="Enter term..."
                      value={paramInput}
                      onChange={e => setParamInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') handleApply(rule);
                      }}
                      sx={{
                        flex: 1,
                        '& input': {
                          fontSize: '0.77rem',
                          fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                        },
                      }}
                    />
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => handleApply(rule)}
                      sx={{ minWidth: 74, fontSize: '0.72rem' }}
                    >
                      Apply
                    </Button>
                  </Box>
                </Collapse>
              </Box>
            ))}
          </Box>
        ))
      )}
    </Box>
  );
}
