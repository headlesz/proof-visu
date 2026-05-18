const API_BASE = process.env.REACT_APP_API_URL || '/api';

async function apiCall(endpoint: string, options?: RequestInit): Promise<any> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response.json();
}

export const api = {
  health: () => apiCall('/health'),

  parse: (formula: string, sessionId = 'default') =>
    apiCall('/parse', {
      method: 'POST',
      body: JSON.stringify({ formula, session_id: sessionId }),
    }),

  setGoal: (formula: string, sessionId = 'default') =>
    apiCall('/new_goal', {
      method: 'POST',
      body: JSON.stringify({ formula, session_id: sessionId }),
    }),

  addPremise: (formula: string, sessionId = 'default') =>
    apiCall('/add_premise', {
      method: 'POST',
      body: JSON.stringify({ formula, session_id: sessionId }),
    }),

  removePremise: (premiseIndex: number, sessionId = 'default') =>
    apiCall('/remove_premise', {
      method: 'POST',
      body: JSON.stringify({ premise_index: premiseIndex, session_id: sessionId }),
    }),

  listRules: (goalId: string, sessionId = 'default') =>
    apiCall(`/list_rules?goal_id=${goalId}&session_id=${sessionId}`),

  applyRule: (goalId: string, rule: string, params: any = {}, sessionId = 'default') =>
    apiCall('/apply_rule', {
      method: 'POST',
      body: JSON.stringify({ goal_id: goalId, rule, params, session_id: sessionId }),
    }),

  undo: (sessionId = 'default') =>
    apiCall('/undo', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  redo: (sessionId = 'default') =>
    apiCall('/redo', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  hint: (goalId: string, useSolver = false, sessionId = 'default') =>
    apiCall(`/hint?goal_id=${goalId}&use_solver=${useSolver}&session_id=${sessionId}`),

  check: (sessionId = 'default') =>
    apiCall(`/check?session_id=${sessionId}`),

  solve: (sessionId = 'default') =>
    apiCall('/solve', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  getState: (sessionId = 'default') =>
    apiCall(`/state?session_id=${sessionId}`),

  getGraph: (sessionId = 'default') =>
    apiCall(`/graph?session_id=${sessionId}`),

  exportProof: (format: 'json' | 'latex' = 'json', sessionId = 'default') =>
    apiCall(`/export?format=${format}&session_id=${sessionId}`),

  reset: (sessionId = 'default') =>
    apiCall('/reset', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),
};
