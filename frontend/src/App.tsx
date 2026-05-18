import React, { useState, useCallback, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  Typography,
  Snackbar,
  Alert,
  Paper,
  useMediaQuery,
  Stack,
  Chip,
} from '@mui/material';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import FormulaInput from './components/FormulaInput';
import GoalsList from './components/GoalsList';
import RulesPanel from './components/RulesPanel';
import ProofGraph from './components/ProofGraph';
import ProofSteps from './components/ProofSteps';
import ControlBar from './components/ControlBar';
import HintDialog from './components/HintDialog';
import ExportDialog from './components/ExportDialog';
import { api } from './services/api';
import { ProofState, RuleInfo, HintResult, GraphData } from './types';
import { RADII } from './theme/radii';
import { COLORS } from './theme/colors';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: COLORS.lavender, contrastText: COLORS.black },
    secondary: { main: COLORS.mint, contrastText: COLORS.black },
    success: { main: COLORS.mint, contrastText: COLORS.black },
    warning: { main: COLORS.butter, contrastText: COLORS.black },
    error: { main: COLORS.blush, contrastText: COLORS.black },
    background: {
      default: COLORS.black,
      paper: COLORS.ink,
    },
    text: {
      primary: COLORS.white,
      secondary: COLORS.muted,
    },
  },
  typography: {
    fontFamily: '"Sora", "Manrope", "Avenir Next", "Segoe UI", sans-serif',
    h5: {
      fontWeight: 700,
      letterSpacing: '-0.015em',
    },
    button: {
      fontWeight: 600,
      letterSpacing: '0.015em',
    },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018))',
          border: `1px solid ${COLORS.line}`,
          boxShadow: '0 18px 42px rgba(0,0,0,0.42)',
          backdropFilter: 'blur(10px)',
          transition: 'transform 240ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 240ms ease, border-color 240ms ease',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: RADII.control,
          transition: 'transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease, border-color 180ms ease',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: RADII.pill,
          fontWeight: 600,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: RADII.control,
          transition: 'box-shadow 200ms ease, border-color 200ms ease',
          '&.Mui-focused': {
            boxShadow: '0 0 0 3px rgba(220, 214, 255, 0.2)',
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: RADII.shell,
          backgroundImage: 'linear-gradient(150deg, rgba(28,28,28,0.98), rgba(12,12,12,0.98))',
        },
      },
    },
  },
});

function App() {
  const [proofState, setProofState] = useState<ProofState | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [hintOpen, setHintOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [exportContent, setExportContent] = useState('');
  const [exportFormat, setExportFormat] = useState<'json' | 'latex'>('json');
  const isMobile = useMediaQuery('(max-width:960px)');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' | 'warning' }>({
    open: false, message: '', severity: 'info',
  });

  const showMessage = useCallback((message: string, severity: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    setSnackbar({ open: true, message, severity });
  }, []);

  const refreshState = useCallback(async () => {
    try {
      const [state, graph] = await Promise.all([api.getState(), api.getGraph()]);
      setProofState(state);
      setGraphData(graph);
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage]);

  const refreshRules = useCallback(async (goalId: string) => {
    try {
      const result = await api.listRules(goalId);
      if (result.success) {
        setRules(result.rules);
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage]);

  useEffect(() => {
    if (selectedGoal) {
      refreshRules(selectedGoal);
    } else {
      setRules([]);
    }
  }, [selectedGoal, refreshRules]);

  const handleSetGoal = useCallback(async (formula: string) => {
    try {
      const result = await api.setGoal(formula);
      if (result.success) {
        setProofState(result.state);
        setSelectedGoal(result.goal_id);
        showMessage('Goal set successfully', 'success');
        await refreshState();
      } else {
        showMessage(result.error, 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage, refreshState]);

  const handleAddPremise = useCallback(async (formula: string) => {
    try {
      const result = await api.addPremise(formula);
      if (result.success) {
        showMessage('Premise added', 'success');
        await refreshState();
        if (selectedGoal) {
          await refreshRules(selectedGoal);
        }
      } else {
        showMessage(result.error, 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [selectedGoal, showMessage, refreshState, refreshRules]);

  const handleRemovePremise = useCallback(async (premiseIndex: number) => {
    try {
      const result = await api.removePremise(premiseIndex);
      if (result.success) {
        setProofState(result.state);
        showMessage('Premise removed', 'info');
        await refreshState();
        if (selectedGoal) {
          await refreshRules(selectedGoal);
        }
      } else {
        showMessage(result.error, 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [selectedGoal, showMessage, refreshState, refreshRules]);

  const handleSelectGoal = useCallback((goalId: string) => {
    setSelectedGoal(goalId);
  }, []);

  const handleApplyRule = useCallback(async (ruleName: string, params?: any) => {
    if (!selectedGoal) {
      showMessage('Select a goal first', 'warning');
      return;
    }
    try {
      const result = await api.applyRule(selectedGoal, ruleName, params);
      if (result.success) {
        setProofState(result.state);
        showMessage(`Applied ${ruleName}`, 'success');
        if (result.new_goal_ids && result.new_goal_ids.length > 0) {
          setSelectedGoal(result.new_goal_ids[0]);
        } else {
          const openGoals = result.state.open_goals;
          if (openGoals.length > 0) {
            setSelectedGoal(openGoals[0]);
          } else {
            setSelectedGoal(null);
          }
        }
        await refreshState();
        if (result.state.is_complete) {
          showMessage('Proof complete!', 'success');
        }
      } else {
        showMessage(result.error, 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [selectedGoal, showMessage, refreshState]);

  const handleUndo = useCallback(async () => {
    try {
      const result = await api.undo();
      if (result.success) {
        setProofState(result.state);
        showMessage('Undone', 'info');
        await refreshState();
      } else {
        showMessage(result.message || 'Nothing to undo', 'info');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage, refreshState]);

  const handleRedo = useCallback(async () => {
    try {
      const result = await api.redo();
      if (result.success) {
        setProofState(result.state);
        showMessage('Redone', 'info');
        await refreshState();
      } else {
        showMessage(result.message || 'Nothing to redo', 'info');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage, refreshState]);

  const handleCheck = useCallback(async () => {
    try {
      const result = await api.check();
      if (result.is_complete) {
        showMessage('Proof is complete!', 'success');
      } else {
        showMessage(result.message, 'warning');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage]);

  const handleSolve = useCallback(async () => {
    try {
      showMessage('Solving...', 'info');
      const result = await api.solve();
      if (result.success) {
        setProofState(result.state);
        await refreshState();
        if (result.is_complete) {
          showMessage(`Proof complete in ${result.steps_taken} step(s)!`, 'success');
        } else {
          showMessage(result.message, 'warning');
        }
        const openGoals = result.state.open_goals;
        if (openGoals && openGoals.length > 0) {
          setSelectedGoal(openGoals[0]);
        } else {
          setSelectedGoal(null);
        }
      } else {
        showMessage(result.error || 'Solve failed', 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage, refreshState]);

  const handleHint = useCallback(async () => {
    if (!selectedGoal) {
      showMessage('Select a goal first', 'warning');
      return;
    }
    try {
      const result = await api.hint(selectedGoal, false);
      setHint(result);
      setHintOpen(true);
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [selectedGoal, showMessage]);

  const handleExport = useCallback(async (format: 'json' | 'latex') => {
    try {
      const result = await api.exportProof(format);
      if (result.success) {
        const content = format === 'json'
          ? JSON.stringify(result.content, null, 2)
          : result.content;
        setExportContent(content);
        setExportFormat(format);
        setExportOpen(true);
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage]);

  const handleReset = useCallback(async () => {
    try {
      await api.reset();
      setProofState(null);
      setGraphData({ nodes: [], edges: [] });
      setSelectedGoal(null);
      setRules([]);
      showMessage('Session reset', 'info');
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          gap: { xs: 1.2, md: 1.8 },
          height: '100dvh',
          p: { xs: 1.2, md: 1.8 },
          overflow: 'hidden',
        }}
      >
        <Paper
          className="flow-panel"
          sx={{
            px: { xs: 1.4, md: 2.2 },
            py: { xs: 1.2, md: 1.4 },
            borderRadius: RADII.shell,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(120deg, rgba(255,255,255,0.08), rgba(220,214,255,0.055))',
              pointerEvents: 'none',
            }}
          />
          <Stack direction="row" spacing={1.2} alignItems="center" sx={{ position: 'relative' }}>
            <Box
              className="pulse-glow"
              sx={{
                width: 36,
                height: 36,
                borderRadius: RADII.control,
                display: 'grid',
                placeItems: 'center',
                bgcolor: 'rgba(191,232,212,0.14)',
                border: '1px solid rgba(191,232,212,0.42)',
              }}
            >
              <AccountTreeIcon sx={{ color: 'secondary.main', fontSize: 20 }} />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="h5" sx={{ fontSize: { xs: '1.05rem', md: '1.32rem' } }}>
                Proof Visualizer Studio
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.2 }}>
                Fluid theorem exploration with interactive proof construction
              </Typography>
            </Box>
            {proofState?.is_complete && (
              <Chip
                label="Proof Complete"
                color="success"
                sx={{
                  fontSize: '0.74rem',
                  px: 1,
                  border: '1px solid rgba(191,232,212,0.48)',
                  bgcolor: 'rgba(191,232,212,0.14)',
                }}
              />
            )}
          </Stack>
        </Paper>

        <Box className="flow-panel" sx={{ animationDelay: '40ms' }}>
          <FormulaInput onSetGoal={handleSetGoal} onAddPremise={handleAddPremise} />
        </Box>

        <Box
          className="flow-panel"
          sx={{
            animationDelay: '90ms',
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            gap: { xs: 1.2, md: 1.6 },
            flex: 1,
            minHeight: 0,
            overflow: 'hidden',
          }}
        >
          <Paper
            sx={{
              width: isMobile ? '100%' : 360,
              minWidth: isMobile ? '100%' : 300,
              maxHeight: isMobile ? '44%' : '100%',
              borderRadius: RADII.shell,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              borderColor: COLORS.lineStrong,
            }}
          >
            <GoalsList
              proofState={proofState}
              selectedGoal={selectedGoal}
              onSelectGoal={handleSelectGoal}
              onRemovePremise={handleRemovePremise}
            />
            <RulesPanel
              rules={rules}
              selectedGoal={selectedGoal}
              onApplyRule={handleApplyRule}
            />
          </Paper>

          <Paper
            sx={{
              flex: 1,
              minHeight: 0,
              borderRadius: RADII.shell,
              p: { xs: 1, md: 1.2 },
              display: 'flex',
              flexDirection: 'column',
              gap: 1.2,
              borderColor: COLORS.lineStrong,
            }}
          >
            <Box sx={{ flex: 2.1, minHeight: 220, borderRadius: RADII.panel, overflow: 'hidden' }}>
              <ProofGraph
                graphData={graphData}
                selectedGoal={selectedGoal}
                onSelectGoal={handleSelectGoal}
              />
            </Box>
            <Box sx={{ flex: 1, minHeight: 140, borderRadius: RADII.panel, overflow: 'hidden' }}>
              <ProofSteps steps={proofState?.steps || []} />
            </Box>
          </Paper>
        </Box>

        <Box className="flow-panel" sx={{ animationDelay: '130ms' }}>
          <ControlBar
            onUndo={handleUndo}
            onRedo={handleRedo}
            onCheck={handleCheck}
            onSolve={handleSolve}
            onHint={handleHint}
            onExportJson={() => handleExport('json')}
            onExportLatex={() => handleExport('latex')}
            onReset={handleReset}
            hasProof={!!proofState?.main_goal}
          />
        </Box>

        <HintDialog
          open={hintOpen}
          hint={hint}
          onClose={() => setHintOpen(false)}
          onApply={(ruleName) => {
            setHintOpen(false);
            handleApplyRule(ruleName);
          }}
        />

        <ExportDialog
          open={exportOpen}
          content={exportContent}
          format={exportFormat}
          onClose={() => setExportOpen(false)}
        />

        <Snackbar
          open={snackbar.open}
          autoHideDuration={3600}
          onClose={() => setSnackbar(s => ({ ...s, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSnackbar(s => ({ ...s, open: false }))}
            severity={snackbar.severity}
            variant="filled"
            sx={{
              width: '100%',
              borderRadius: RADII.control,
              border: `1px solid ${COLORS.lineStrong}`,
              backdropFilter: 'blur(8px)',
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default App;
