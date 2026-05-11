export interface GoalNode {
  id: string;
  formula: string;
  formula_ast: any;
  assumptions: string[];
  assumptions_ast: any[];
  is_proven: boolean;
  parent_id: string | null;
  rule_applied: string | null;
  children_ids: string[];
  label: string;
}

export interface ProofStep {
  id: number;
  rule: string;
  goal_id: string;
  sources: string[];
  formula: string | null;
  new_goal_ids: string[];
  note: string;
  params: Record<string, any>;
}

export interface ProofState {
  main_goal: string | null;
  premises: string[];
  goals: Record<string, GoalNode>;
  steps: ProofStep[];
  is_complete: boolean;
  open_goals: string[];
}

export interface RuleInfo {
  name: string;
  description: string;
  category: string;
}

export interface HintResult {
  success: boolean;
  hint?: string;
  suggested_rule?: RuleInfo;
  solver_info?: string;
  error?: string;
}

export interface GraphData {
  nodes: Array<{
    data: {
      id: string;
      label: string;
      is_proven: boolean;
      rule: string;
      goal_label: string;
    };
    classes: string;
  }>;
  edges: Array<{
    data: {
      id: string;
      source: string;
      target: string;
      label: string;
    };
  }>;
}
