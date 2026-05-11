import React from 'react';
import { Box, Button, Divider, Paper, Tooltip } from '@mui/material';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import CheckIcon from '@mui/icons-material/Check';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import CodeIcon from '@mui/icons-material/Code';
import DescriptionIcon from '@mui/icons-material/Description';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import { RADII } from '../theme/radii';

interface Props {
  onUndo: () => void;
  onRedo: () => void;
  onCheck: () => void;
  onSolve: () => void;
  onHint: () => void;
  onExportJson: () => void;
  onExportLatex: () => void;
  onReset: () => void;
  hasProof: boolean;
}

const baseBtnSx = {
  height: 34,
  px: 1.2,
  borderRadius: RADII.control,
  fontSize: '0.74rem',
  whiteSpace: 'nowrap',
};

export default function ControlBar({
  onUndo, onRedo, onCheck, onSolve, onHint, onExportJson, onExportLatex, onReset, hasProof,
}: Props) {
  return (
    <Paper
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.7,
        px: { xs: 1, md: 1.3 },
        py: 0.95,
        borderRadius: RADII.shell,
        borderColor: 'rgba(244,162,97,0.2)',
        flexWrap: 'wrap',
      }}
    >
      <Tooltip title="Undo (Ctrl+Z)">
        <span>
          <Button size="small" startIcon={<UndoIcon />} onClick={onUndo} disabled={!hasProof} sx={baseBtnSx}>
            Undo
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Redo (Ctrl+Y)">
        <span>
          <Button size="small" startIcon={<RedoIcon />} onClick={onRedo} disabled={!hasProof} sx={baseBtnSx}>
            Redo
          </Button>
        </span>
      </Tooltip>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.4, borderColor: 'rgba(183,200,202,0.2)' }} />

      <Tooltip title="Check if proof is complete">
        <span>
          <Button
            size="small"
            startIcon={<CheckIcon />}
            onClick={onCheck}
            disabled={!hasProof}
            color="success"
            variant="outlined"
            sx={baseBtnSx}
          >
            Check
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Automatically solve the proof">
        <span>
          <Button
            size="small"
            startIcon={<AutoFixHighIcon />}
            onClick={onSolve}
            disabled={!hasProof}
            color="secondary"
            variant="contained"
            sx={{
              ...baseBtnSx,
              bgcolor: 'secondary.main',
              color: '#0f2224',
              boxShadow: '0 10px 22px rgba(42,157,143,0.3)',
              '&:hover': {
                bgcolor: '#38b2a4',
              },
            }}
          >
            Solve
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Get a hint for the selected goal">
        <span>
          <Button
            size="small"
            startIcon={<LightbulbIcon />}
            onClick={onHint}
            disabled={!hasProof}
            color="warning"
            variant="outlined"
            sx={baseBtnSx}
          >
            Hint
          </Button>
        </span>
      </Tooltip>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.4, borderColor: 'rgba(183,200,202,0.2)' }} />

      <Tooltip title="Export as JSON">
        <span>
          <Button size="small" startIcon={<CodeIcon />} onClick={onExportJson} disabled={!hasProof} sx={baseBtnSx}>
            JSON
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Export as LaTeX">
        <span>
          <Button size="small" startIcon={<DescriptionIcon />} onClick={onExportLatex} disabled={!hasProof} sx={baseBtnSx}>
            LaTeX
          </Button>
        </span>
      </Tooltip>

      <Box sx={{ flexGrow: 1 }} />

      <Tooltip title="Reset proof session">
        <span>
          <Button
            size="small"
            startIcon={<RestartAltIcon />}
            onClick={onReset}
            color="error"
            variant="outlined"
            sx={baseBtnSx}
          >
            Reset
          </Button>
        </span>
      </Tooltip>
    </Paper>
  );
}
