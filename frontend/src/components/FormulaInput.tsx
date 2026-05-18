import React, { useState, useCallback, useRef } from 'react';
import {
  Box, TextField, Button, Paper, Typography, ToggleButtonGroup, ToggleButton,
  Chip, Tooltip,
} from '@mui/material';
import FunctionsIcon from '@mui/icons-material/Functions';
import AddIcon from '@mui/icons-material/Add';
import { RADII } from '../theme/radii';

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
  { label: '∉', symbol: '∉', title: 'Not element of' },
  { label: '⊆', symbol: '⊆', title: 'Subset' },
  { label: '∩', symbol: '∩', title: 'Intersect' },
  { label: '∪', symbol: '∪', title: 'Union' },
  { label: 'ᶜ', symbol: 'ᶜ', title: 'Complement' },
  { label: '⊥', symbol: '⊥', title: 'Bottom (False)' },
  { label: '⊤', symbol: '⊤', title: 'Top (True)' },
];

export default function FormulaInput({ onSetGoal, onAddPremise }: Props) {
  const [formula, setFormula] = useState('');
  const [mode, setMode] = useState<'goal' | 'premise'>('goal');
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleSubmit = useCallback(() => {
    if (!formula.trim()) return;
    if (mode === 'goal') {
      onSetGoal(formula.trim());
    } else {
      onAddPremise(formula.trim());
    }
  }, [formula, mode, onSetGoal, onAddPremise]);

  const insertSymbol = useCallback((symbol: string) => {
    const input = inputRef.current;
    if (!input) {
      setFormula(prev => prev + symbol);
      return;
    }

    const start = input.selectionStart ?? formula.length;
    const end = input.selectionEnd ?? start;
    const nextFormula = `${formula.slice(0, start)}${symbol}${formula.slice(end)}`;
    const nextCursor = start + symbol.length;

    setFormula(nextFormula);
    window.requestAnimationFrame(() => {
      input.focus();
      input.setSelectionRange(nextCursor, nextCursor);
    });
  }, [formula]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <Paper
      sx={{
        p: { xs: 1.1, md: 1.4 },
        borderRadius: RADII.shell,
        borderColor: 'rgba(42,157,143,0.24)',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(120deg, rgba(42,157,143,0.08), rgba(244,162,97,0.03))',
          pointerEvents: 'none',
        }}
      />

      <Box sx={{ position: 'relative' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 1.1, flexWrap: 'wrap' }}>
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: RADII.icon,
              display: 'grid',
              placeItems: 'center',
              bgcolor: 'rgba(244,162,97,0.16)',
              border: '1px solid rgba(244,162,97,0.44)',
            }}
          >
            <FunctionsIcon sx={{ color: 'primary.main', fontSize: 17 }} />
          </Box>
          <Typography
            variant="subtitle2"
            sx={{
              fontSize: '0.73rem',
              textTransform: 'uppercase',
              letterSpacing: 1.15,
              color: 'text.secondary',
            }}
          >
            Formula Entry
          </Typography>

          <ToggleButtonGroup
            size="small"
            value={mode}
            exclusive
            onChange={(_, v) => v && setMode(v)}
            sx={{
              ml: 'auto',
              '& .MuiToggleButton-root': {
                px: 1.8,
                fontSize: '0.74rem',
                borderColor: 'rgba(244,162,97,0.28)',
                color: 'text.secondary',
                '&.Mui-selected': {
                  color: '#0f1f24',
                  bgcolor: 'primary.main',
                  borderColor: 'rgba(244,162,97,0.95)',
                },
              },
            }}
          >
            <ToggleButton value="goal">Set Goal</ToggleButton>
            <ToggleButton value="premise">Add Premise</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: { xs: 'wrap', md: 'nowrap' } }}>
          <TextField
            fullWidth
            size="small"
            placeholder={mode === 'goal' ? 'Try: A ∩ Aᶜ = ∅' : 'Enter premise formula'}
            value={formula}
            inputRef={inputRef}
            onChange={e => setFormula(e.target.value)}
            onKeyDown={handleKeyDown}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                fontSize: '0.86rem',
                bgcolor: 'rgba(11,20,24,0.42)',
              },
            }}
          />
          <Button
            variant="contained"
            onClick={handleSubmit}
            startIcon={mode === 'goal' ? <FunctionsIcon /> : <AddIcon />}
            disabled={!formula.trim()}
            sx={{
              minWidth: 138,
              height: 40,
              boxShadow: '0 10px 24px rgba(244,162,97,0.25)',
              bgcolor: 'primary.main',
              color: '#102027',
              '&:hover': {
                bgcolor: '#f7b47d',
                boxShadow: '0 14px 26px rgba(244,162,97,0.28)',
              },
            }}
          >
            {mode === 'goal' ? 'Set Goal' : 'Add Premise'}
          </Button>
        </Box>

        <Box sx={{ display: 'flex', gap: 0.55, mt: 1.15, flexWrap: 'wrap' }}>
          {SYMBOL_SHORTCUTS.map(s => (
            <Tooltip key={s.symbol} title={s.title} arrow>
              <Chip
                label={s.label}
                onMouseDown={e => e.preventDefault()}
                onClick={() => insertSymbol(s.symbol)}
                sx={{
                  fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                  fontSize: '0.82rem',
                  height: 26,
                  cursor: 'pointer',
                  color: 'text.secondary',
                  borderColor: 'rgba(183,200,202,0.32)',
                  bgcolor: 'rgba(13,26,31,0.45)',
                  transition: 'transform 180ms ease, border-color 180ms ease, color 180ms ease, background-color 180ms ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    color: 'primary.main',
                    borderColor: 'rgba(244,162,97,0.62)',
                    bgcolor: 'rgba(244,162,97,0.14)',
                  },
                }}
                variant="outlined"
              />
            </Tooltip>
          ))}
        </Box>
      </Box>
    </Paper>
  );
}
