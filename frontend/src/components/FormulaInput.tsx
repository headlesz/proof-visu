import React, { useState, useCallback } from 'react';
import {
  Box, TextField, Button, Paper, Typography, ToggleButtonGroup, ToggleButton,
  Chip, Tooltip,
} from '@mui/material';
import FunctionsIcon from '@mui/icons-material/Functions';
import AddIcon from '@mui/icons-material/Add';

interface Props {
  onSetGoal: (formula: string) => void;
  onAddPremise: (formula: string) => void;
}

const SYMBOL_SHORTCUTS = [
  { label: '∧', symbol: '∧', title: 'And' },
  { label: '∨', symbol: '∨', title: 'Or' },
  { label: '¬', symbol: '¬', title: 'Not' },
  { label: '→', symbol: '→', title: 'Implies' },
  { label: '↔', symbol: '↔', title: 'Iff' },
  { label: '∀', symbol: '∀', title: 'For all' },
  { label: '∃', symbol: '∃', title: 'Exists' },
  { label: '∈', symbol: '∈', title: 'Element of' },
  { label: '⊆', symbol: '⊆', title: 'Subset' },
  { label: '∩', symbol: '∩', title: 'Intersect' },
  { label: '∪', symbol: '∪', title: 'Union' },
  { label: '⊥', symbol: '⊥', title: 'Bottom (False)' },
  { label: '⊤', symbol: '⊤', title: 'Top (True)' },
];

export default function FormulaInput({ onSetGoal, onAddPremise }: Props) {
  const [formula, setFormula] = useState('');
  const [mode, setMode] = useState<'goal' | 'premise'>('goal');

  const handleSubmit = useCallback(() => {
    if (!formula.trim()) return;
    if (mode === 'goal') {
      onSetGoal(formula.trim());
    } else {
      onAddPremise(formula.trim());
    }
  }, [formula, mode, onSetGoal, onAddPremise]);

  const insertSymbol = useCallback((symbol: string) => {
    setFormula(prev => prev + symbol);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <Paper
      elevation={0}
      sx={{
        px: 2, py: 1.5,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 0,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
        <FunctionsIcon sx={{ color: 'primary.main', fontSize: 20 }} />
        <Typography variant="subtitle2" sx={{ color: 'text.secondary', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Formula Input
        </Typography>
        <ToggleButtonGroup
          size="small"
          value={mode}
          exclusive
          onChange={(_, v) => v && setMode(v)}
          sx={{ ml: 'auto' }}
        >
          <ToggleButton value="goal" sx={{ px: 2, py: 0.25, fontSize: '0.75rem' }}>Set Goal</ToggleButton>
          <ToggleButton value="premise" sx={{ px: 2, py: 0.25, fontSize: '0.75rem' }}>Add Premise</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <TextField
          fullWidth
          size="small"
          placeholder={mode === 'goal' ? 'Enter goal formula, e.g. (p ∧ q) → (q ∧ p)' : 'Enter premise formula'}
          value={formula}
          onChange={e => setFormula(e.target.value)}
          onKeyDown={handleKeyDown}
          sx={{
            '& .MuiOutlinedInput-root': {
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '0.9rem',
            },
          }}
        />
        <Button
          variant="contained"
          onClick={handleSubmit}
          startIcon={mode === 'goal' ? <FunctionsIcon /> : <AddIcon />}
          disabled={!formula.trim()}
          sx={{ minWidth: 120, whiteSpace: 'nowrap' }}
        >
          {mode === 'goal' ? 'Set Goal' : 'Add Premise'}
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 0.5, mt: 1, flexWrap: 'wrap' }}>
        {SYMBOL_SHORTCUTS.map(s => (
          <Tooltip key={s.symbol} title={s.title} arrow>
            <Chip
              label={s.label}
              size="small"
              variant="outlined"
              onClick={() => insertSymbol(s.symbol)}
              sx={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: '0.85rem',
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'rgba(124,77,255,0.15)' },
              }}
            />
          </Tooltip>
        ))}
      </Box>
    </Paper>
  );
}
