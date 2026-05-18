import React from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box, Chip,
} from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import { HintResult } from '../types';
import { RADII } from '../theme/radii';
import { COLORS } from '../theme/colors';

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
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, pb: 1 }}>
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: RADII.icon,
            display: 'grid',
            placeItems: 'center',
            bgcolor: 'rgba(244,230,168,0.13)',
            border: '1px solid rgba(244,230,168,0.38)',
          }}
        >
          <LightbulbIcon sx={{ color: 'warning.main', fontSize: 16 }} />
        </Box>
        <Box>
          <Typography sx={{ fontSize: '1rem', fontWeight: 700 }}>Hint</Typography>
          <Typography variant="caption" color="text.secondary">
            Next best move from the current goal context
          </Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {hint.hint && (
          <Typography variant="body1" sx={{ mb: 2.1, lineHeight: 1.6 }}>
            {hint.hint}
          </Typography>
        )}
        {hint.suggested_rule && (
          <Box
            sx={{
              mb: 2,
              p: 1.1,
              borderRadius: RADII.panel,
              border: '1px solid rgba(220,214,255,0.32)',
              bgcolor: 'rgba(255,255,255,0.04)',
            }}
          >
            <Chip
              label={hint.suggested_rule.name.replace(/_/g, ' ')}
              sx={{
                fontFamily: '"DM Mono", "JetBrains Mono", monospace',
                color: COLORS.black,
                bgcolor: 'primary.main',
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.1 }}>
              {hint.suggested_rule.description}
            </Typography>
          </Box>
        )}
        {hint.solver_info && (
          <Typography variant="body2" sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
            Solver: {hint.solver_info}
          </Typography>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 2.3, pb: 1.7 }}>
        <Button onClick={onClose}>Close</Button>
        {hint.suggested_rule && (
          <Button
            variant="contained"
            onClick={() => onApply(hint.suggested_rule!.name)}
            sx={{
              bgcolor: 'primary.main',
              color: COLORS.black,
              '&:hover': { bgcolor: COLORS.white },
            }}
          >
            Apply Suggested Rule
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
