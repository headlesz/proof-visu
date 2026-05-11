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

export default function ControlBar({
  onUndo, onRedo, onCheck, onSolve, onHint, onExportJson, onExportLatex, onReset, hasProof,
}: Props) {
  return (
    <Paper
      elevation={0}
      sx={{
        display: 'flex', alignItems: 'center', gap: 0.5,
        px: 2, py: 0.75,
        borderTop: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 0,
      }}
    >
      <Tooltip title="Undo (Ctrl+Z)">
        <span>
          <Button size="small" startIcon={<UndoIcon />} onClick={onUndo} disabled={!hasProof}>
            Undo
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Redo (Ctrl+Y)">
        <span>
          <Button size="small" startIcon={<RedoIcon />} onClick={onRedo} disabled={!hasProof}>
            Redo
          </Button>
        </span>
      </Tooltip>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

      <Tooltip title="Check if proof is complete">
        <span>
          <Button size="small" startIcon={<CheckIcon />} onClick={onCheck} disabled={!hasProof} color="success">
            Check Proof
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Automatically solve the proof">
        <span>
          <Button size="small" startIcon={<AutoFixHighIcon />} onClick={onSolve} disabled={!hasProof} color="secondary">
            Solve Proof
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Get a hint for the selected goal">
        <span>
          <Button size="small" startIcon={<LightbulbIcon />} onClick={onHint} disabled={!hasProof} color="warning">
            Hint
          </Button>
        </span>
      </Tooltip>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

      <Tooltip title="Export as JSON">
        <span>
          <Button size="small" startIcon={<CodeIcon />} onClick={onExportJson} disabled={!hasProof}>
            JSON
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Export as LaTeX">
        <span>
          <Button size="small" startIcon={<DescriptionIcon />} onClick={onExportLatex} disabled={!hasProof}>
            LaTeX
          </Button>
        </span>
      </Tooltip>

      <Box sx={{ flexGrow: 1 }} />

      <Tooltip title="Reset proof session">
        <span>
          <Button size="small" startIcon={<RestartAltIcon />} onClick={onReset} color="error">
            Reset
          </Button>
        </span>
      </Tooltip>
    </Paper>
  );
}
