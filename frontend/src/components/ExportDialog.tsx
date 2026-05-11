import React, { useCallback } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import { RADII } from '../theme/radii';

interface Props {
  open: boolean;
  content: string;
  format: 'json' | 'latex';
  onClose: () => void;
}

export default function ExportDialog({ open, content, format, onClose }: Props) {
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content);
  }, [content]);

  const handleDownload = useCallback(() => {
    const ext = format === 'json' ? 'json' : 'tex';
    const mime = format === 'json' ? 'application/json' : 'text/plain';
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `proof.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [content, format]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontWeight: 700, pb: 1 }}>
        Export Proof ({format.toUpperCase()})
      </DialogTitle>
      <DialogContent>
        <Box
          sx={{
            bgcolor: 'rgba(8,16,20,0.82)',
            borderRadius: RADII.panel,
            p: 1.5,
            maxHeight: 400,
            overflow: 'auto',
            border: '1px solid rgba(183,200,202,0.22)',
          }}
        >
          <Typography
            component="pre"
            sx={{
              fontFamily: '"DM Mono", "JetBrains Mono", monospace',
              fontSize: '0.79rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              m: 0,
              color: '#cfe1e2',
            }}
          >
            {content}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 2.2, pb: 1.7 }}>
        <Button onClick={onClose}>Close</Button>
        <Button startIcon={<ContentCopyIcon />} onClick={handleCopy} variant="outlined">
          Copy
        </Button>
        <Button
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
          variant="contained"
          sx={{
            bgcolor: 'secondary.main',
            color: '#102027',
            '&:hover': { bgcolor: '#38b2a4' },
          }}
        >
          Download
        </Button>
      </DialogActions>
    </Dialog>
  );
}
