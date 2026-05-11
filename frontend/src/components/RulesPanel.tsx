import React, { useState } from 'react';
import {
  Box, Typography, Button, Collapse, TextField, Paper, Chip, Tooltip,
} from '@mui/material';
import GavelIcon from '@mui/icons-material/Gavel';
import { RuleInfo } from '../types';

interface Props {
  rules: RuleInfo[];
  selectedGoal: string | null;
  onApplyRule: (ruleName: string, params?: any) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  propositional: '#7c4dff',
  quantifier: '#00e5ff',
  set_theory: '#ff9100',
  induction: '#69f0ae',
  general: '#90a4ae',
};

export default function RulesPanel({ rules, selectedGoal, onApplyRule }: Props) {
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [paramInput, setParamInput] = useState('');

  if (!selectedGoal) {
    return (
      <Paper
        elevation={0}
        sx={{ flex: 1, p: 2, borderRadius: 0, borderTop: '1px solid rgba(255,255,255,0.06)' }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', fontSize: '0.8rem' }}>
          Select an open goal to see applicable rules.
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
    <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
      <Box sx={{ px: 2, py: 1, borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 1 }}>
        <GavelIcon sx={{ fontSize: 16, color: 'secondary.main' }} />
        <Typography variant="subtitle2" sx={{ color: 'text.secondary', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Available Rules ({rules.length})
        </Typography>
      </Box>

      {rules.length === 0 ? (
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
            No applicable rules for this goal.
          </Typography>
        </Box>
      ) : (
        Object.entries(grouped).map(([category, catRules]) => (
          <Box key={category}>
            <Box sx={{ px: 2, py: 0.5 }}>
              <Chip
                label={category.replace('_', ' ')}
                size="small"
                sx={{
                  fontSize: '0.6rem', height: 18,
                  backgroundColor: `${CATEGORY_COLORS[category] || '#666'}22`,
                  color: CATEGORY_COLORS[category] || '#666',
                  borderColor: CATEGORY_COLORS[category] || '#666',
                }}
                variant="outlined"
              />
            </Box>
            {catRules.map(rule => (
              <Box key={rule.name} sx={{ px: 1.5, py: 0.25 }}>
                <Tooltip title={rule.description} placement="right" arrow>
                  <Button
                    fullWidth
                    size="small"
                    variant={expandedRule === rule.name ? 'contained' : 'text'}
                    onClick={() => handleApply(rule)}
                    sx={{
                      justifyContent: 'flex-start',
                      fontFamily: '"JetBrains Mono", monospace',
                      fontSize: '0.75rem',
                      py: 0.5,
                      textAlign: 'left',
                      color: expandedRule === rule.name ? 'white' : CATEGORY_COLORS[rule.category] || 'text.primary',
                    }}
                  >
                    {rule.name.replace(/_/g, ' ')}
                  </Button>
                </Tooltip>
                <Collapse in={expandedRule === rule.name}>
                  <Box sx={{ px: 1, pb: 1, display: 'flex', gap: 0.5 }}>
                    <TextField
                      size="small"
                      placeholder="Enter term..."
                      value={paramInput}
                      onChange={e => setParamInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') handleApply(rule);
                      }}
                      sx={{ flex: 1, '& input': { fontSize: '0.8rem', fontFamily: '"JetBrains Mono", monospace' } }}
                    />
                    <Button size="small" variant="contained" onClick={() => handleApply(rule)}>
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
