import React from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box, Chip,
} from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import { HintResult } from '../types';

interface Props {
  open: boolean;
  hint: HintResult | null;
  onClose: () => void;
  onApply: (ruleName: string) => void;
}

export default function HintDialog({ open, hint, onClose, onApply }: Props) {
  if (!hint) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <LightbulbIcon sx={{ color: '#ff9100' }} />
        Hint
      </DialogTitle>
      <DialogContent>
        {hint.hint && (
          <Typography variant="body1" sx={{ mb: 2 }}>
            {hint.hint}
          </Typography>
        )}
        {hint.suggested_rule && (
          <Box sx={{ mb: 2 }}>
            <Chip
              label={hint.suggested_rule.name.replace(/_/g, ' ')}
              color="primary"
              sx={{ fontFamily: '"JetBrains Mono", monospace', mr: 1 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {hint.suggested_rule.description}
            </Typography>
          </Box>
        )}
        {hint.solver_info && (
          <Typography variant="body2" sx={{ color: '#00e5ff', fontStyle: 'italic' }}>
            Solver: {hint.solver_info}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {hint.suggested_rule && (
          <Button
            variant="contained"
            onClick={() => onApply(hint.suggested_rule!.name)}
          >
            Apply Suggested Rule
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
