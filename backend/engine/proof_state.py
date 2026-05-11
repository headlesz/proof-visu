"""
Proof state management. Tracks goals, assumptions, proof steps, and history.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from parser.ast_nodes import ASTNode
import json
import copy


@dataclass
class GoalNode:
    """Represents a single goal (subgoal) in the proof."""
    id: str
    formula: ASTNode
    assumptions: List[ASTNode] = field(default_factory=list)
    is_proven: bool = False
    parent_id: Optional[str] = None
    rule_applied: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    manual_elim_history: List[str] = field(default_factory=list)
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "formula": str(self.formula),
            "formula_ast": self.formula.to_dict(),
            "assumptions": [str(a) for a in self.assumptions],
            "assumptions_ast": [a.to_dict() for a in self.assumptions],
            "is_proven": self.is_proven,
            "parent_id": self.parent_id,
            "rule_applied": self.rule_applied,
            "children_ids": self.children_ids,
            "manual_elim_history": self.manual_elim_history,
            "label": self.label,
        }


@dataclass
class ProofStep:
    """Records a single inference step in the proof."""
    id: int
    rule: str
    goal_id: str
    sources: List[str] = field(default_factory=list)
    result_formula: Optional[ASTNode] = None
    new_goal_ids: List[str] = field(default_factory=list)
    note: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule": self.rule,
            "goal_id": self.goal_id,
            "sources": self.sources,
            "formula": str(self.result_formula) if self.result_formula else None,
            "new_goal_ids": self.new_goal_ids,
            "note": self.note,
            "params": self.params,
        }


class ProofState:
    """Manages the entire proof state including goals, steps, and history."""

    def __init__(self):
        self.goals: Dict[str, GoalNode] = {}
        self.premises: List[ASTNode] = []
        self.main_goal: Optional[str] = None
        self.steps: List[ProofStep] = []
        self._goal_counter: int = 0
        self._step_counter: int = 0
        self._history: List[dict] = []
        self._redo_stack: List[dict] = []
        self._fresh_var_counter: int = 0

    def _snapshot(self) -> dict:
        """Create a snapshot of the current state for undo."""
        return {
            "goals": {k: copy.deepcopy(v) for k, v in self.goals.items()},
            "premises": list(self.premises),
            "main_goal": self.main_goal,
            "steps": list(self.steps),
            "goal_counter": self._goal_counter,
            "step_counter": self._step_counter,
            "fresh_var_counter": self._fresh_var_counter,
        }

    def _restore(self, snapshot: dict):
        """Restore state from a snapshot."""
        self.goals = snapshot["goals"]
        self.premises = snapshot["premises"]
        self.main_goal = snapshot["main_goal"]
        self.steps = snapshot["steps"]
        self._goal_counter = snapshot["goal_counter"]
        self._step_counter = snapshot["step_counter"]
        self._fresh_var_counter = snapshot["fresh_var_counter"]

    def save_checkpoint(self):
        """Save current state before making changes."""
        self._history.append(self._snapshot())
        self._redo_stack.clear()

    def undo(self) -> bool:
        """Undo the last action. Returns True if successful."""
        if not self._history:
            return False
        self._redo_stack.append(self._snapshot())
        self._restore(self._history.pop())
        return True

    def redo(self) -> bool:
        """Redo the last undone action. Returns True if successful."""
        if not self._redo_stack:
            return False
        self._history.append(self._snapshot())
        self._restore(self._redo_stack.pop())
        return True

    def fresh_goal_id(self) -> str:
        """Generate a unique goal identifier."""
        self._goal_counter += 1
        return f"G{self._goal_counter}"

    def fresh_step_id(self) -> int:
        """Generate a unique step identifier."""
        self._step_counter += 1
        return self._step_counter

    def fresh_variable(self, base: str = "x") -> str:
        """Generate a fresh variable name."""
        self._fresh_var_counter += 1
        return f"{base}_{self._fresh_var_counter}"

    @staticmethod
    def dedupe_assumptions(assumptions: List[ASTNode]) -> List[ASTNode]:
        """Deduplicate assumptions by structural string, preserving first-seen order."""
        seen = set()
        deduped: List[ASTNode] = []
        for a in assumptions or []:
            sig = str(a)
            if sig in seen:
                continue
            seen.add(sig)
            deduped.append(a)
        return deduped

    def add_goal(self, formula: ASTNode, assumptions: List[ASTNode] = None,
                 parent_id: str = None, label: str = "") -> GoalNode:
        """Add a new goal to the proof."""
        inherited_manual_history: List[str] = []
        if parent_id and parent_id in self.goals:
            inherited_manual_history = list(self.goals[parent_id].manual_elim_history)
        gid = self.fresh_goal_id()
        node = GoalNode(
            id=gid,
            formula=formula,
            assumptions=self.dedupe_assumptions(assumptions or []),
            parent_id=parent_id,
            manual_elim_history=inherited_manual_history,
            label=label,
        )
        self.goals[gid] = node
        if parent_id and parent_id in self.goals:
            self.goals[parent_id].children_ids.append(gid)
        return node

    def set_main_goal(self, formula: ASTNode) -> GoalNode:
        """Set the main theorem to prove."""
        self.save_checkpoint()
        self.goals.clear()
        self.steps.clear()
        self._goal_counter = 0
        self._step_counter = 0
        node = self.add_goal(formula, assumptions=list(self.premises), label="Main Goal")
        self.main_goal = node.id
        return node

    def add_premise(self, formula: ASTNode):
        """Add a premise to the proof context."""
        self.save_checkpoint()
        self.premises.append(formula)
        for goal in self.goals.values():
            if not goal.is_proven:
                goal.assumptions = self.dedupe_assumptions(list(goal.assumptions) + [formula])

    def mark_proven(self, goal_id: str, rule: str = ""):
        """Mark a goal as proven."""
        if goal_id in self.goals:
            self.goals[goal_id].is_proven = True
            self.goals[goal_id].rule_applied = rule

    def add_step(self, rule: str, goal_id: str, sources: List[str] = None,
                 result_formula: ASTNode = None, new_goal_ids: List[str] = None,
                 note: str = "", params: Dict = None) -> ProofStep:
        """Record a proof step."""
        step = ProofStep(
            id=self.fresh_step_id(),
            rule=rule,
            goal_id=goal_id,
            sources=sources or [],
            result_formula=result_formula,
            new_goal_ids=new_goal_ids or [],
            note=note,
            params=params or {},
        )
        self.steps.append(step)
        return step

    def open_goals(self) -> List[GoalNode]:
        """Return all unproven goals."""
        return [g for g in self.goals.values() if not g.is_proven]

    def is_complete(self) -> bool:
        """Check if the proof is complete (all goals proven)."""
        if not self.main_goal:
            return False
        return all(g.is_proven for g in self.goals.values())

    def to_dict(self) -> dict:
        """Serialize the entire proof state."""
        return {
            "main_goal": self.main_goal,
            "premises": [str(p) for p in self.premises],
            "goals": {k: v.to_dict() for k, v in self.goals.items()},
            "steps": [s.to_dict() for s in self.steps],
            "is_complete": self.is_complete(),
            "open_goals": [g.id for g in self.open_goals()],
        }

    def to_export_json(self) -> dict:
        """Export proof in the specification's JSON format."""
        theorem = str(self.goals[self.main_goal].formula) if self.main_goal else ""
        return {
            "theorem": theorem,
            "premises": [str(p) for p in self.premises],
            "proof_steps": [s.to_dict() for s in self.steps],
        }

    def to_latex(self) -> str:
        """Export proof as LaTeX."""
        lines = []
        theorem = str(self.goals[self.main_goal].formula) if self.main_goal else "?"
        lines.append("\\begin{proof}")
        lines.append(f"  \\textbf{{Theorem:}} ${self.goals[self.main_goal].formula.to_latex() if self.main_goal else '?'}$")
        lines.append("")
        if self.premises:
            lines.append("  \\textbf{Premises:}")
            for p in self.premises:
                lines.append(f"    \\item ${p.to_latex()}$")
            lines.append("")
        lines.append("  \\textbf{Proof Steps:}")
        lines.append("  \\begin{enumerate}")
        for step in self.steps:
            formula_str = step.result_formula.to_latex() if step.result_formula else "..."
            lines.append(f"    \\item [{step.rule}] ${formula_str}$ {step.note}")
        lines.append("  \\end{enumerate}")
        lines.append("\\end{proof}")
        return "\n".join(lines)
