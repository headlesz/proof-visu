"""
Proof state management. Tracks goals, assumptions, proof steps, and history.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from parser.ast_nodes import (
    ASTNode, And, Or, Implies, Iff, Equals, ElementOf, NotElementOf,
    Union, Intersect, Complement, Bottom,
)
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
        if not self.main_goal or self.main_goal not in self.goals:
            return "\\begin{proof}\n  No theorem has been set.\n\\end{proof}"

        lines = []
        steps_by_goal = self._steps_by_goal()
        lines.append("\\begin{proof}")
        lines.append(f"  \\textbf{{Theorem:}} ${self.goals[self.main_goal].formula.to_latex()}$")
        lines.append("")
        if self.premises:
            lines.append("  \\textbf{Premises:}")
            lines.append("  \\begin{itemize}")
            for p in self.premises:
                lines.append(f"    \\item ${p.to_latex()}$")
            lines.append("  \\end{itemize}")
            lines.append("")
        lines.append("  \\textbf{Proof.}")
        lines.append("  \\begin{enumerate}")
        lines.extend(self._render_goal_latex(self.main_goal, steps_by_goal, indent=2, is_root=True))
        lines.append("  \\end{enumerate}")
        lines.append("\\end{proof}")
        return "\n".join(lines)

    def _steps_by_goal(self) -> Dict[str, List[ProofStep]]:
        steps_by_goal: Dict[str, List[ProofStep]] = {}
        for step in self.steps:
            steps_by_goal.setdefault(step.goal_id, []).append(step)
        return steps_by_goal

    def _render_goal_latex(self, goal_id: str, steps_by_goal: Dict[str, List[ProofStep]],
                           indent: int, is_root: bool = False) -> List[str]:
        goal = self.goals[goal_id]
        prefix = "  " * indent
        lines = [f"{prefix}\\item {self._goal_intro_sentence(goal, is_root)}"]

        for step in self._local_derivation_steps(goal, steps_by_goal):
            lines.append(f"{prefix}  {self._local_step_sentence(step)}")

        main_step = self._main_step_for_goal(goal, steps_by_goal)
        if goal.children_ids:
            lines.append(f"{prefix}  {self._rule_sentence(goal, main_step)}")
            lines.append(f"{prefix}  \\begin{{enumerate}}")
            for child_id in goal.children_ids:
                lines.extend(self._render_goal_latex(child_id, steps_by_goal, indent + 2))
            lines.append(f"{prefix}  \\end{{enumerate}}")
        else:
            lines.append(f"{prefix}  {self._closure_sentence(goal, main_step)}")
        return lines

    def _goal_intro_sentence(self, goal: GoalNode, is_root: bool) -> str:
        if is_root:
            return f"We prove ${goal.formula.to_latex()}$."

        label = goal.label or ""
        if label.startswith("Case: "):
            case_formula = self._case_formula_from_label(goal, label[len("Case: "):])
            if case_formula:
                return f"\\textbf{{Case ${case_formula.to_latex()}$:}} Prove ${goal.formula.to_latex()}$."
            return f"\\textbf{{Case {self._escape_latex_text(label[len('Case: '):])}:}} Prove ${goal.formula.to_latex()}$."

        if label in {"Forward direction", "Backward direction"}:
            return f"\\textbf{{{label}:}} Prove ${goal.formula.to_latex()}$."

        if label.startswith("Assume ") or label.startswith("Prove "):
            return f"It remains to prove ${goal.formula.to_latex()}$."

        if label:
            return f"{self._escape_latex_text(label)}: prove ${goal.formula.to_latex()}$."
        return f"Prove ${goal.formula.to_latex()}$."

    def _case_formula_from_label(self, goal: GoalNode, case_text: str) -> Optional[ASTNode]:
        for assumption in goal.assumptions:
            if str(assumption) == case_text:
                return assumption
        return None

    def _local_derivation_steps(self, goal: GoalNode,
                                steps_by_goal: Dict[str, List[ProofStep]]) -> List[ProofStep]:
        local_steps: List[ProofStep] = []
        for step in steps_by_goal.get(goal.id, []):
            if step.new_goal_ids:
                continue
            if step.rule == goal.rule_applied:
                continue
            local_steps.append(step)
        return local_steps

    def _main_step_for_goal(self, goal: GoalNode,
                            steps_by_goal: Dict[str, List[ProofStep]]) -> Optional[ProofStep]:
        for step in reversed(steps_by_goal.get(goal.id, [])):
            if step.rule == goal.rule_applied:
                return step
        return None

    def _rule_sentence(self, goal: GoalNode, step: Optional[ProofStep]) -> str:
        rule = goal.rule_applied or ""
        f = goal.formula

        if rule == "iff_intro" and isinstance(f, Iff):
            return (
                "By biconditional introduction, it suffices to prove both "
                f"${Implies(f.left, f.right).to_latex()}$ and ${Implies(f.right, f.left).to_latex()}$."
            )
        if rule == "implies_intro" and isinstance(f, Implies):
            return f"Assume ${f.left.to_latex()}$; it remains to prove ${f.right.to_latex()}$."
        if rule == "and_intro" and isinstance(f, And):
            return f"By conjunction introduction, prove ${f.left.to_latex()}$ and ${f.right.to_latex()}$."
        if rule == "or_intro_left" and isinstance(f, Or):
            return f"By left disjunction introduction, it suffices to prove ${f.left.to_latex()}$."
        if rule == "or_intro_right" and isinstance(f, Or):
            return f"By right disjunction introduction, it suffices to prove ${f.right.to_latex()}$."
        if rule == "or_elim":
            source = self._first_assumption(goal, Or)
            source_text = f" on ${source.to_latex()}$" if source else ""
            return f"By disjunction elimination{source_text}, prove the goal in each case."
        if rule == "classical_cases":
            case_formula = self._case_formula_from_step(step)
            if case_formula:
                return f"By excluded middle, split into the cases ${case_formula.to_latex()}$ and its negation."
            return "By excluded middle, split into complementary cases."
        if rule == "equality_intro" and isinstance(f, Equals):
            return f"By extensionality, prove ${f.left.to_latex()} \\subseteq {f.right.to_latex()}$ and ${f.right.to_latex()} \\subseteq {f.left.to_latex()}$."
        if rule == "subset_intro":
            return "By subset introduction, take an arbitrary element of the left side and prove it belongs to the right side."
        if rule == "intersect_intro" and isinstance(f, ElementOf) and isinstance(f.set_expr, Intersect):
            return f"By intersection introduction, prove ${f.element.to_latex()} \\in {f.set_expr.left.to_latex()}$ and ${f.element.to_latex()} \\in {f.set_expr.right.to_latex()}$."
        if rule == "union_intro_left" and isinstance(f, ElementOf) and isinstance(f.set_expr, Union):
            return f"By left union introduction, it suffices to prove ${f.element.to_latex()} \\in {f.set_expr.left.to_latex()}$."
        if rule == "union_intro_right" and isinstance(f, ElementOf) and isinstance(f.set_expr, Union):
            return f"By right union introduction, it suffices to prove ${f.element.to_latex()} \\in {f.set_expr.right.to_latex()}$."
        if rule == "union_elim":
            source = self._first_union_membership(goal)
            source_text = f" on ${source.to_latex()}$" if source else ""
            return f"By union elimination{source_text}, prove the goal in each case."
        if rule == "complement_intro" and isinstance(f, ElementOf) and isinstance(f.set_expr, Complement):
            return f"By the definition of complement, it suffices to prove ${NotElementOf(f.element, f.set_expr.operand).to_latex()}$."
        if rule == "not_complement_intro" and isinstance(f, NotElementOf) and isinstance(f.set_expr, Complement):
            return f"By the definition of complement, it suffices to prove ${ElementOf(f.element, f.set_expr.operand).to_latex()}$."
        if rule == "not_element_intro" and isinstance(f, NotElementOf):
            return f"To prove nonmembership, assume ${ElementOf(f.element, f.set_expr).to_latex()}$ and derive a contradiction."
        if rule == "not_intro":
            return "To prove the negation, assume the positive statement and derive a contradiction."
        if step:
            return f"Apply {self._rule_label(step.rule)}."
        return "It remains to prove the following subgoals."

    def _closure_sentence(self, goal: GoalNode, step: Optional[ProofStep]) -> str:
        rule = goal.rule_applied or ""
        formula = goal.formula.to_latex()
        if rule == "assumption":
            return f"This is one of the assumptions, so ${formula}$ follows."
        if rule == "contradiction":
            return f"The assumptions are contradictory, so ${formula}$ follows."
        if rule == "emptyset_elim":
            return f"An element of the empty set is assumed, so ${formula}$ follows."
        if rule == "not_elim":
            return f"By double-negation elimination, ${formula}$ follows."
        if rule in {"and_elim_left", "and_elim_right", "intersect_elim", "complement_elim",
                    "not_complement_elim", "implies_elim"}:
            return f"By {self._rule_label(rule)}, derive ${formula}$."
        if step:
            return f"By {self._rule_label(step.rule)}, ${formula}$ follows."
        return f"Thus ${formula}$ is proven."

    def _local_step_sentence(self, step: ProofStep) -> str:
        formula = step.result_formula.to_latex() if step.result_formula else "\\ldots"
        if step.rule == "implies_elim":
            return f"By modus ponens, derive ${formula}$."
        if step.rule in {"and_elim_left", "and_elim_right"}:
            return f"By conjunction elimination, derive ${formula}$."
        if step.rule == "intersect_elim":
            return f"By intersection elimination, add the component memberships from ${formula}$."
        if step.rule == "complement_elim":
            return f"By complement elimination, derive ${formula}$."
        if step.rule == "not_complement_elim":
            return f"By complement nonmembership elimination, derive ${formula}$."
        return f"By {self._rule_label(step.rule)}, derive ${formula}$."

    def _case_formula_from_step(self, step: Optional[ProofStep]) -> Optional[ASTNode]:
        if not step:
            return None
        formula = step.params.get("formula") or step.params.get("case_formula")
        if not formula:
            return None
        for gid in step.new_goal_ids:
            goal = self.goals.get(gid)
            if not goal:
                continue
            for assumption in goal.assumptions:
                if str(assumption) == str(formula):
                    return assumption
        return None

    def _first_assumption(self, goal: GoalNode, cls):
        for assumption in goal.assumptions:
            if isinstance(assumption, cls):
                return assumption
        return None

    def _first_union_membership(self, goal: GoalNode) -> Optional[ElementOf]:
        for assumption in goal.assumptions:
            if isinstance(assumption, ElementOf) and isinstance(assumption.set_expr, Union):
                return assumption
        return None

    def _rule_label(self, rule: str) -> str:
        return self._escape_latex_text(rule.replace("_", " "))

    def _escape_latex_text(self, text: str) -> str:
        return (
            text.replace("\\", "\\textbackslash{}")
                .replace("&", "\\&")
                .replace("%", "\\%")
                .replace("$", "\\$")
                .replace("#", "\\#")
                .replace("_", "\\_")
                .replace("{", "\\{")
                .replace("}", "\\}")
        )
