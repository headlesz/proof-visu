import React, { useCallback } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';

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
      <DialogTitle>Export Proof ({format.toUpperCase()})</DialogTitle>
      <DialogContent>
        <Box
          sx={{
            bgcolor: '#0d1117',
            borderRadius: 1,
            p: 2,
            maxHeight: 400,
            overflow: 'auto',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <Typography
            component="pre"
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '0.8rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              m: 0,
            }}
          >
            {content}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button startIcon={<ContentCopyIcon />} onClick={handleCopy}>
          Copy
        </Button>
        <Button startIcon={<DownloadIcon />} onClick={handleDownload} variant="contained">
          Download
        </Button>
      </DialogActions>
    </Dialog>
  );
}
