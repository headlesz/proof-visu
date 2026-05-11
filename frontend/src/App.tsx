import React, { useState, useCallback, useEffect } from 'react';
import {
  ThemeProvider, createTheme, CssBaseline, Box, AppBar, Toolbar, Typography,
  IconButton, Snackbar, Alert, Tooltip,
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

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7c4dff' },
    secondary: { main: '#00e5ff' },
    background: { default: '#0d1117', paper: '#161b22' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.06)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500 },
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
      } else {
        showMessage(result.error, 'error');
      }
    } catch (e: any) {
      showMessage(e.message, 'error');
    }
  }, [showMessage, refreshState]);

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
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <Toolbar variant="dense">
            <Tooltip title="Interactive Proof Visualizer">
              <IconButton edge="start" color="inherit" sx={{ mr: 1 }}>
                <AccountTreeIcon />
              </IconButton>
            </Tooltip>
            <Typography variant="h6" sx={{ flexGrow: 1, fontSize: '1rem' }}>
              Proof Visualizer
            </Typography>
            {proofState?.is_complete && (
              <Typography variant="body2" sx={{ color: '#4caf50', fontWeight: 600, mr: 2 }}>
                PROOF COMPLETE
              </Typography>
            )}
          </Toolbar>
        </AppBar>

        <FormulaInput onSetGoal={handleSetGoal} onAddPremise={handleAddPremise} />

        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden', gap: 0 }}>
          {/* Left sidebar: Goals + Rules */}
          <Box sx={{ width: 320, minWidth: 280, display: 'flex', flexDirection: 'column', borderRight: '1px solid rgba(255,255,255,0.06)' }}>
            <GoalsList
              proofState={proofState}
              selectedGoal={selectedGoal}
              onSelectGoal={handleSelectGoal}
            />
            <RulesPanel
              rules={rules}
              selectedGoal={selectedGoal}
              onApplyRule={handleApplyRule}
            />
          </Box>

          {/* Main area: Graph + Steps */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <Box sx={{ flex: 2, minHeight: 200 }}>
              <ProofGraph
                graphData={graphData}
                selectedGoal={selectedGoal}
                onSelectGoal={handleSelectGoal}
              />
            </Box>
            <Box sx={{ flex: 1, minHeight: 150, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <ProofSteps steps={proofState?.steps || []} />
            </Box>
          </Box>
        </Box>

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
          autoHideDuration={4000}
          onClose={() => setSnackbar(s => ({ ...s, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSnackbar(s => ({ ...s, open: false }))}
            severity={snackbar.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default App;
