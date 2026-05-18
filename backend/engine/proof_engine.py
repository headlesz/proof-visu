"""
Main proof engine. Orchestrates parsing, rule application, state management, and hints.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import copy
from parser.formula_parser import FormulaParser, ParseError
from parser.ast_nodes import (
    ASTNode, And, Or, Not, Implies, Iff, Forall, Exists,
    Equals, Union, Intersect, ElementOf, Subset, Superset, Bottom,
    Complement, NotElementOf, EmptySet,
)
from .proof_state import ProofState, GoalNode
from .rules import (
    RULES_BY_NAME, get_applicable_rules, RuleError, InferenceRule
)


class ProofEngine:
    """High-level interface for managing proof sessions."""

    def __init__(self):
        self.parser = FormulaParser()
        self.state = ProofState()

    def parse_formula(self, formula_str: str) -> dict:
        """Parse a formula string and return its AST."""
        try:
            ast = self.parser.parse(formula_str)
            return {
                "success": True,
                "formula": str(ast),
                "ast": ast.to_dict(),
            }
        except ParseError as e:
            return {
                "success": False,
                "error": e.message,
                "line": e.line,
                "column": e.column,
            }

    def set_goal(self, formula_str: str) -> dict:
        """Set the main goal of the proof."""
        try:
            ast = self.parser.parse(formula_str)
        except ParseError as e:
            return {"success": False, "error": e.message}

        goal = self.state.set_main_goal(ast)
        return {
            "success": True,
            "goal_id": goal.id,
            "state": self.state.to_dict(),
        }

    def add_premise(self, formula_str: str) -> dict:
        """Add a premise to the proof context."""
        try:
            ast = self.parser.parse(formula_str)
        except ParseError as e:
            return {"success": False, "error": e.message}

        self.state.add_premise(ast)
        return {
            "success": True,
            "state": self.state.to_dict(),
        }

    def remove_premise(self, premise_index: int) -> dict:
        """Remove a premise from the proof context."""
        removed = self.state.remove_premise(premise_index)
        if removed is None:
            return {"success": False, "error": f"Premise index {premise_index} not found"}

        return {
            "success": True,
            "removed_premise": str(removed),
            "state": self.state.to_dict(),
        }

    def list_rules(self, goal_id: str) -> dict:
        """List applicable rules for a given goal."""
        if goal_id not in self.state.goals:
            return {"success": False, "error": f"Goal {goal_id} not found"}

        goal = self.state.goals[goal_id]
        if goal.is_proven:
            return {"success": True, "rules": [], "message": "Goal already proven"}

        applicable = get_applicable_rules(self.state, goal)
        filtered: List[InferenceRule] = []
        for r in applicable:
            # Rules panel applies elim rules without source selection. Hide
            # options that would repeat an elim on the same source in this path.
            if self._is_manual_redundant_elim(goal, r.name):
                continue
            filtered.append(r)
        return {
            "success": True,
            "rules": [r.to_dict() for r in filtered],
        }

    def apply_rule(self, goal_id: str, rule_name: str, params: Dict = None) -> dict:
        """Apply a specific inference rule to a goal."""
        if goal_id not in self.state.goals:
            return {"success": False, "error": f"Goal {goal_id} not found"}

        goal = self.state.goals[goal_id]
        if goal.is_proven:
            return {"success": False, "error": f"Goal {goal_id} is already proven"}

        if rule_name not in RULES_BY_NAME:
            return {"success": False, "error": f"Unknown rule: {rule_name}"}

        rule = RULES_BY_NAME[rule_name]
        if not rule.is_applicable(self.state, goal, params):
            return {"success": False, "error": f"Rule {rule_name} is not applicable to this goal"}

        apply_params = dict(params or {})
        elim_choice = self._select_manual_elim_source(goal, rule_name, apply_params)
        elim_source = elim_choice[1] if elim_choice else None
        if rule_name in {"union_elim", "intersect_elim"} and elim_choice is None:
            return {"success": False, "error": f"No selectable source remains for rule {rule_name}"}
        if elim_choice is not None and "source_idx" not in apply_params:
            apply_params["source_idx"] = elim_choice[0]

        try:
            new_goal_ids = rule.apply(self.state, goal, apply_params)
            self._dedupe_all_goal_assumptions()
            if elim_source is not None:
                marker = self._elim_marker(rule_name, elim_source)
                self._record_manual_elim_marker(goal_id, marker, new_goal_ids)
            return {
                "success": True,
                "new_goal_ids": new_goal_ids,
                "state": self.state.to_dict(),
            }
        except RuleError as e:
            return {"success": False, "error": str(e)}

    def _elim_marker(self, rule_name: str, source: ASTNode) -> str:
        return f"{rule_name}|{source}"

    def _select_manual_elim_source(self, goal: GoalNode, rule_name: str,
                                   params: Dict = None) -> Optional[tuple]:
        """Pick a non-redundant elim source as (index, assumption)."""
        p = params or {}
        source_idx = p.get("source_idx", None)

        if source_idx is not None:
            if 0 <= source_idx < len(goal.assumptions):
                source = goal.assumptions[source_idx]
                marker = self._elim_marker(rule_name, source)
                if marker in goal.manual_elim_history:
                    return None
                return source_idx, source
            return None

        if rule_name == "intersect_elim":
            for i, a in enumerate(goal.assumptions):
                if isinstance(a, ElementOf) and isinstance(a.set_expr, Intersect):
                    marker = self._elim_marker(rule_name, a)
                    if marker in goal.manual_elim_history:
                        continue
                    return i, a
        if rule_name == "union_elim":
            for i, a in enumerate(goal.assumptions):
                if isinstance(a, ElementOf) and isinstance(a.set_expr, Union):
                    marker = self._elim_marker(rule_name, a)
                    if marker in goal.manual_elim_history:
                        continue
                    return i, a
        return None

    def _is_manual_redundant_elim(self, goal: GoalNode, rule_name: str, params: Dict = None) -> bool:
        if rule_name not in {"union_elim", "intersect_elim"}:
            return False
        return self._select_manual_elim_source(goal, rule_name, params) is None

    def _record_manual_elim_marker(self, goal_id: str, marker: str, new_goal_ids: List[str]):
        goal = self.state.goals.get(goal_id)
        if goal and marker not in goal.manual_elim_history:
            goal.manual_elim_history.append(marker)
        for gid in new_goal_ids or []:
            child = self.state.goals.get(gid)
            if child and marker not in child.manual_elim_history:
                child.manual_elim_history.append(marker)

    def undo(self) -> dict:
        """Undo the last action."""
        success = self.state.undo()
        return {
            "success": success,
            "state": self.state.to_dict(),
            "message": "Undo successful" if success else "Nothing to undo",
        }

    def redo(self) -> dict:
        """Redo the last undone action."""
        success = self.state.redo()
        return {
            "success": success,
            "state": self.state.to_dict(),
            "message": "Redo successful" if success else "Nothing to redo",
        }

    def check_proof(self) -> dict:
        """Check if the proof is complete."""
        is_complete = self.state.is_complete()
        open_goals = self.state.open_goals()
        return {
            "success": True,
            "is_complete": is_complete,
            "open_goals": [g.to_dict() for g in open_goals],
            "message": "Proof complete!" if is_complete else f"{len(open_goals)} goal(s) remaining",
        }

    def get_hint(self, goal_id: str) -> dict:
        """Get a hint for the given goal. Uses heuristics and optionally Z3."""
        if goal_id not in self.state.goals:
            return {"success": False, "error": f"Goal {goal_id} not found"}

        goal = self.state.goals[goal_id]
        if goal.is_proven:
            return {"success": True, "hint": "This goal is already proven."}

        applicable = [
            r for r in get_applicable_rules(self.state, goal)
            if not self._is_manual_redundant_elim(goal, r.name)
        ]
        if not applicable:
            return {"success": True, "hint": "No applicable rules found. Try adding premises or using a different approach."}

        # Heuristic priority: assumption > contradiction > intro rules > elim rules
        for r in applicable:
            if r.name == "assumption":
                return {
                    "success": True,
                    "hint": f"The goal '{goal.formula}' matches an assumption. Apply 'assumption' to close it.",
                    "suggested_rule": r.to_dict(),
                }

        for r in applicable:
            if r.name == "contradiction":
                return {
                    "success": True,
                    "hint": "A contradiction exists in your assumptions. Apply 'contradiction' to close the goal.",
                    "suggested_rule": r.to_dict(),
                }

        # Prefer introduction rules for the goal's connective
        intro_rules = [r for r in applicable if "intro" in r.name]
        if intro_rules:
            r = intro_rules[0]
            return {
                "success": True,
                "hint": f"Try applying '{r.name}': {r.description}",
                "suggested_rule": r.to_dict(),
            }

        # Elimination rules
        elim_rules = [r for r in applicable if "elim" in r.name]
        if elim_rules:
            r = elim_rules[0]
            return {
                "success": True,
                "hint": f"Try applying '{r.name}': {r.description}",
                "suggested_rule": r.to_dict(),
            }

        # Fallback
        r = applicable[0]
        return {
            "success": True,
            "hint": f"Consider applying '{r.name}': {r.description}",
            "suggested_rule": r.to_dict(),
        }

    def get_hint_with_solver(self, goal_id: str) -> dict:
        """Enhanced hint using Z3 solver."""
        basic_hint = self.get_hint(goal_id)

        try:
            from solvers.z3_solver import Z3Solver
            goal = self.state.goals.get(goal_id)
            if goal:
                solver = Z3Solver()
                result = solver.check_validity(goal.formula, goal.assumptions)
                if result.get("valid"):
                    basic_hint["solver_info"] = "Z3 confirms this goal is provable from the assumptions."
                elif result.get("error"):
                    basic_hint["solver_info"] = f"Z3 could not determine: {result['error']}"
                else:
                    basic_hint["solver_info"] = "Z3 suggests this goal may not follow from the current assumptions."
        except ImportError:
            basic_hint["solver_info"] = "Z3 solver not available."
        except Exception as e:
            basic_hint["solver_info"] = f"Solver error: {str(e)}"

        return basic_hint

    def solve(self, max_steps: int = 200) -> dict:
        """Goal-directed proof solver with backtracking.

        Analyzes each goal's formula structure to pick the right rule,
        dramatically pruning the search space compared to blind DFS.
        """
        if not self.state.main_goal:
            return {"success": False, "error": "No goal set"}

        if self.state.steps:
            recovered = self._recover_from_scratch(max_steps)
            if recovered:
                return recovered

        primary = self._attempt_solve(max_steps)
        if primary.get("is_complete"):
            return primary

        # If manual interaction committed to a dead-end branch (for example,
        # choosing one intro branch where the other was needed), run a fresh
        # solve from theorem + premises so "Solve" can still complete solvable
        # problems from the UI.
        recovered = self._recover_from_scratch(max_steps)
        if recovered:
            return recovered

        return primary

    def _recover_from_scratch(self, max_steps: int = 200) -> Optional[dict]:
        theorem_goal = self.state.goals.get(self.state.main_goal)
        if theorem_goal is None:
            return None
        scratch = ProofEngine()
        scratch.state.premises = copy.deepcopy(self.state.premises)
        scratch.state.set_main_goal(copy.deepcopy(theorem_goal.formula))
        recovered = scratch._attempt_solve(max_steps)
        if recovered.get("is_complete"):
            self.state = scratch.state
            recovered["message"] = (
                f"Proof complete in {recovered['steps_taken']} step(s)! "
                "(recovered from a manual dead-end by re-solving from theorem)"
            )
            recovered["state"] = self.state.to_dict()
            return recovered

        return None

    def _attempt_solve(self, max_steps: int = 200) -> dict:
        """Run one solving attempt from the current state."""
        self.state.save_checkpoint()
        self._solve_steps = 0
        self._solve_max = max_steps
        # Memoize abstract frontier states so we do not re-explore the same
        # proof-search state at an equal-or-worse remaining depth.
        self._state_depth_seen: Dict[tuple, int] = {}
        # Memoize failed local subgoals. If a goal signature cannot be solved
        # at depth D, it cannot be solved at any depth <= D.
        self._failed_goal_depth: Dict[str, int] = {}

        snapshot = self.state._snapshot()
        search_depth = max(1, max_steps)
        if self._solve_all_goals(search_depth):
            return {
                "success": True,
                "is_complete": True,
                "steps_taken": self._solve_steps,
                "state": self.state.to_dict(),
                "message": f"Proof complete in {self._solve_steps} step(s)!",
            }

        self.state._restore(snapshot)
        return {
            "success": True,
            "is_complete": False,
            "steps_taken": 0,
            "state": self.state.to_dict(),
            "message": f"Solver could not complete the proof. "
                       f"{len(self.state.open_goals())} goal(s) remaining.",
        }

    def _solve_all_goals(self, depth: int) -> bool:
        """Solve all remaining open goals."""
        if self.state.is_complete():
            return True
        if depth <= 0 or self._solve_steps >= self._solve_max:
            return False

        open_goals = self.state.open_goals()
        if not open_goals:
            return self.state.is_complete()

        state_sig = self._state_sig()
        seen_depth = self._state_depth_seen.get(state_sig, -1)
        if seen_depth >= depth:
            return False
        self._state_depth_seen[state_sig] = depth

        # Prefer goals that can close immediately, then structurally simpler
        # goals. This avoids repeatedly deepening into hard branches while an
        # easy assumption-close goal is available.
        open_goals.sort(key=self._goal_priority)
        goal_id = open_goals[0].id
        return self._solve_goal(goal_id, depth)

    def _solve_goal(self, goal_id: str, depth: int) -> bool:
        """Solve a single goal using goal-directed rule selection."""
        if depth <= 0 or self._solve_steps >= self._solve_max:
            return False

        goal = self.state.goals.get(goal_id)
        if not goal or goal.is_proven:
            return self._solve_all_goals(depth)

        sig = self._goal_sig(goal)
        seen_fail_depth = self._failed_goal_depth.get(sig, -1)
        if seen_fail_depth >= depth:
            return False

        # If a descendant goal repeats an ancestor goal's abstract state, we
        # are in a branch-local cycle (typically from elim/intros ping-pong).
        if self._repeats_ancestor_state(goal):
            return False

        solved = self._try_solve_goal(goal_id, goal, depth)
        if not solved:
            prev = self._failed_goal_depth.get(sig, -1)
            if depth > prev:
                self._failed_goal_depth[sig] = depth
        return solved

    def _try_solve_goal(self, goal_id: str, goal, depth: int) -> bool:
        """Core goal-directed solving logic.

        Strategy:
        1. Close immediately if possible (assumption, contradiction)
        2. For deterministic intro rules (and_intro, implies_intro, etc.),
           apply them directly — they have exactly one decomposition.
        3. For goals needing enrichment, apply ONE elim rule at a time,
           then recurse (which re-checks assumption and structural rules).
        4. For choice rules, try each option with backtracking.
        """
        f = goal.formula
        assumption_strs = set(str(a) for a in goal.assumptions)

        # Phase 1: Try to close immediately
        if str(f) in assumption_strs:
            return self._try_rule('assumption', goal_id, depth)

        if self._try_rule('emptyset_elim', goal_id, depth):
            return True

        if self._try_rule('contradiction', goal_id, depth):
            return True

        # Phase 2: Determine structural rules
        structural = self._structural_rules(f, goal)

        # Deterministic rules (exactly one way to decompose) — apply directly
        deterministic = {'and_intro', 'implies_intro', 'not_intro', 'iff_intro',
                         'forall_intro', 'exists_intro', 'equality_intro',
                         'subset_intro', 'intersect_intro', 'complement_intro',
                         'not_complement_intro', 'not_element_intro'}

        for rule_name in structural:
            if rule_name in deterministic:
                return self._try_rule(rule_name, goal_id, depth)

        # Phase 3: Try non-branching elim rules first (intersect_elim,
        # and_elim add to assumptions without creating new goals).
        # These are "free" enrichments that don't branch the search.
        elim_rules = self._useful_elim_rules(goal)
        non_branching = [r for r in elim_rules if r not in ('union_elim', 'or_elim')]
        for rule_name in non_branching:
            if self._try_rule(rule_name, goal_id, depth):
                return True

        branching = [r for r in elim_rules if r in ('union_elim', 'or_elim')]

        # For disjunction-style goals without an immediate witness for either
        # intro branch, case-splitting first is usually more productive.
        if self._prefer_branching_before_intro(goal, structural, assumption_strs):
            for rule_name in branching:
                if self._try_rule(rule_name, goal_id, depth):
                    return True

        classical_candidates = self._classical_case_candidates(goal)
        prefer_classical = bool(classical_candidates) and self._prefer_branching_before_intro(
            goal, structural, assumption_strs
        )
        if prefer_classical:
            for case_formula in classical_candidates:
                if self._try_rule('classical_cases', goal_id, depth,
                                  {"formula": str(case_formula)}):
                    return True

        # Phase 4: Try structural choice rules (union_intro, or_intro)
        for rule_name in structural:
            if self._try_rule(rule_name, goal_id, depth):
                return True

        # Phase 5: Try branching elim rules (union_elim, or_elim) as fallback
        for rule_name in branching:
            if self._try_rule(rule_name, goal_id, depth):
                return True

        # Phase 6: Classical fallback for tautologies that need excluded
        # middle, such as (p → q) ↔ (¬p ∨ q).
        if not prefer_classical:
            for case_formula in classical_candidates:
                if self._try_rule('classical_cases', goal_id, depth,
                                  {"formula": str(case_formula)}):
                    return True

        return False

    def _structural_rules(self, f, goal) -> List[str]:
        """Return the intro rule names appropriate for the goal's formula."""
        if isinstance(f, And):
            return ['and_intro']
        if isinstance(f, Implies):
            return ['implies_intro']
        if isinstance(f, Not):
            return ['not_intro']
        if isinstance(f, Iff):
            return ['iff_intro']
        if isinstance(f, Or):
            # Prefer the side that matches an assumption
            left_str = str(f.left)
            right_str = str(f.right)
            assumption_strs = set(str(a) for a in goal.assumptions)
            if left_str in assumption_strs:
                return ['or_intro_left', 'or_intro_right']
            if right_str in assumption_strs:
                return ['or_intro_right', 'or_intro_left']
            return ['or_intro_left', 'or_intro_right']
        if isinstance(f, Forall):
            return ['forall_intro']
        if isinstance(f, Exists):
            return ['exists_intro']
        if isinstance(f, Equals):
            return ['equality_intro']
        if isinstance(f, Subset):
            return ['subset_intro']
        if isinstance(f, Superset):
            return ['subset_intro']
        if isinstance(f, ElementOf):
            rhs = f.set_expr
            if isinstance(rhs, Complement):
                return ['complement_intro']
            if isinstance(rhs, Intersect):
                return ['intersect_intro']
            if isinstance(rhs, Union):
                # Check which side of the union is more promising
                elem = f.element
                assumption_strs = set(str(a) for a in goal.assumptions)
                left_goal = str(ElementOf(elem, rhs.left))
                right_goal = str(ElementOf(elem, rhs.right))
                if left_goal in assumption_strs:
                    return ['union_intro_left', 'union_intro_right']
                if right_goal in assumption_strs:
                    return ['union_intro_right', 'union_intro_left']
                return ['union_intro_left', 'union_intro_right']
            # Simple element-of: no structural rule, try elims
            return []
        if isinstance(f, NotElementOf):
            if isinstance(f.set_expr, Complement):
                return ['not_complement_intro']
            return ['not_element_intro']
        return []

    def _useful_elim_rules(self, goal) -> List[str]:
        """Return elim rules that would produce genuinely new assumptions."""
        result = []
        assumption_strs = set(str(a) for a in goal.assumptions)

        for a in goal.assumptions:
            if isinstance(a, ElementOf) and isinstance(a.set_expr, EmptySet):
                if 'emptyset_elim' not in result:
                    result.append('emptyset_elim')
            if isinstance(a, And):
                if str(a.left) not in assumption_strs:
                    if 'and_elim_left' not in result:
                        result.append('and_elim_left')
                if str(a.right) not in assumption_strs:
                    if 'and_elim_right' not in result:
                        result.append('and_elim_right')
            if isinstance(a, Or):
                if str(a.left) not in assumption_strs or str(a.right) not in assumption_strs:
                    if 'or_elim' not in result:
                        result.append('or_elim')
            if isinstance(a, ElementOf):
                rhs = a.set_expr
                if isinstance(rhs, Intersect):
                    elem = a.element
                    l_str = str(ElementOf(elem, rhs.left))
                    r_str = str(ElementOf(elem, rhs.right))
                    if l_str not in assumption_strs or r_str not in assumption_strs:
                        if 'intersect_elim' not in result:
                            result.append('intersect_elim')
                if isinstance(rhs, Union):
                    # Only offer union_elim if it would produce new info
                    elem = a.element
                    left_str = str(ElementOf(elem, rhs.left))
                    right_str = str(ElementOf(elem, rhs.right))
                    # Offer union_elim only if we don't already have both branches
                    if left_str not in assumption_strs or right_str not in assumption_strs:
                        # Additional check: union_elim is only useful if eliminating
                        # could help close the goal. Check if either branch contains
                        # the goal's element-set, or matches the goal directly.
                        if self._union_elim_useful(goal.formula, a):
                            if 'union_elim' not in result:
                                result.append('union_elim')
                if isinstance(rhs, Complement):
                    derived = str(NotElementOf(a.element, rhs.operand))
                    if derived not in assumption_strs:
                        if 'complement_elim' not in result:
                            result.append('complement_elim')
                if str(NotElementOf(a.element, a.set_expr)) in assumption_strs:
                    if 'contradiction' not in result:
                        result.append('contradiction')
            if isinstance(a, NotElementOf):
                if isinstance(a.set_expr, Complement):
                    derived = str(ElementOf(a.element, a.set_expr.operand))
                    if derived not in assumption_strs:
                        if 'not_complement_elim' not in result:
                            result.append('not_complement_elim')
                if str(ElementOf(a.element, a.set_expr)) in assumption_strs:
                    if 'contradiction' not in result:
                        result.append('contradiction')
            if isinstance(a, Implies):
                # Check if the antecedent is in assumptions
                if str(a.left) in assumption_strs and str(a.right) not in assumption_strs:
                    if 'implies_elim' not in result:
                        result.append('implies_elim')
            if isinstance(a, Not):
                inner = a.operand
                if inner and str(inner) in assumption_strs:
                    if 'contradiction' not in result:
                        result.append('contradiction')

        return result

    def _union_elim_useful(self, goal_formula, union_assumption) -> bool:
        """Check if union_elim on this union could plausibly help prove the goal.

        A union x ∈ A ∪ B is worth eliminating if:
        - The goal involves x and a set built from A or B
        - The goal's element matches the union's element
        - Some elimination chain could derive the goal
        """
        if isinstance(goal_formula, Bottom):
            return True
        # If the goal isn't an ElementOf, union_elim probably doesn't help
        if not isinstance(goal_formula, ElementOf):
            return False
        # Element must match (same x being talked about)
        if str(goal_formula.element) != str(union_assumption.element):
            return False
        # The union assumption is about the same element as the goal — useful
        return True

    def _try_rule(self, rule_name: str, goal_id: str, depth: int,
                  params: Dict = None) -> bool:
        """Try applying a rule; if it succeeds and all goals solve, return True.
        Otherwise backtrack."""
        rule = RULES_BY_NAME.get(rule_name)
        if not rule:
            return False

        goal = self.state.goals.get(goal_id)
        if not goal or goal.is_proven:
            return self._solve_all_goals(depth)

        if not rule.is_applicable(self.state, goal, params):
            return False

        snapshot = self.state._snapshot()
        old_steps = self._solve_steps
        old_failed_goal_depth = dict(self._failed_goal_depth)

        try:
            goal = self.state.goals[goal_id]
            rule.apply(self.state, goal, params)
            self._dedupe_all_goal_assumptions()
            self._solve_steps += 1

            if self._solve_all_goals(depth - 1):
                return True

            self.state._restore(snapshot)
            self._solve_steps = old_steps
            self._failed_goal_depth = old_failed_goal_depth
            return False
        except Exception:
            self.state._restore(snapshot)
            self._solve_steps = old_steps
            self._failed_goal_depth = old_failed_goal_depth
            return False

    def _goal_sig(self, goal) -> str:
        """Signature for a single goal (formula + deduplicated assumptions)."""
        return self._goal_sig_parts(goal.formula, goal.assumptions)

    def _goal_sig_parts(self, formula, assumptions) -> str:
        assumption_sig = tuple(sorted(set(str(a) for a in assumptions)))
        return str(formula) + '||' + str(assumption_sig)

    def _state_sig(self) -> tuple:
        """Canonical signature for the current frontier of open goals."""
        return tuple(sorted(self._goal_sig(g) for g in self.state.open_goals()))

    def _repeats_ancestor_state(self, goal: GoalNode) -> bool:
        """Check whether this goal repeats an ancestor's abstract state."""
        sig = self._goal_sig(goal)
        parent_id = goal.parent_id
        while parent_id:
            parent = self.state.goals.get(parent_id)
            if not parent:
                break
            if self._goal_sig(parent) == sig:
                return True
            parent_id = parent.parent_id
        return False

    def _goal_priority(self, goal: GoalNode) -> tuple:
        """Ordering heuristic for which open goal to solve next."""
        assumption_strs = set(str(a) for a in goal.assumptions)
        closes_by_assumption = str(goal.formula) in assumption_strs
        structural = self._structural_rules(goal.formula, goal)
        deterministic = {'and_intro', 'implies_intro', 'not_intro', 'iff_intro',
                         'forall_intro', 'exists_intro', 'equality_intro',
                         'subset_intro', 'intersect_intro', 'complement_intro',
                         'not_complement_intro', 'not_element_intro'}
        has_deterministic = any(r in deterministic for r in structural)
        has_structural = bool(structural)
        return (
            0 if closes_by_assumption else 1,
            0 if has_deterministic else (1 if has_structural else 2),
            len(set(str(a) for a in goal.assumptions)),
            goal.id,
        )

    def _prefer_branching_before_intro(self, goal: GoalNode,
                                       structural: List[str],
                                       assumption_strs: set) -> bool:
        """Whether branching elim should run before intro choices."""
        if not structural:
            return False

        f = goal.formula
        if isinstance(f, Or):
            left_str = str(f.left)
            right_str = str(f.right)
            return left_str not in assumption_strs and right_str not in assumption_strs

        if isinstance(f, ElementOf) and isinstance(f.set_expr, Union):
            left_goal = str(ElementOf(f.element, f.set_expr.left))
            right_goal = str(ElementOf(f.element, f.set_expr.right))
            return left_goal not in assumption_strs and right_goal not in assumption_strs

        return False

    def _classical_case_candidates(self, goal: GoalNode) -> List[ASTNode]:
        """Return formulas worth splitting on with excluded middle."""
        f = goal.formula
        assumption_strs = set(str(a) for a in goal.assumptions)
        candidates: List[ASTNode] = []

        if isinstance(f, Or):
            for assumption in goal.assumptions:
                if not isinstance(assumption, Implies):
                    continue
                if f.left == Not(assumption.left) and f.right == assumption.right:
                    candidates.append(assumption.left)
                if f.right == Not(assumption.left) and f.left == assumption.right:
                    candidates.append(assumption.left)

            if isinstance(f.left, Not):
                candidates.append(f.left.operand)
            if isinstance(f.right, Not):
                candidates.append(f.right.operand)

        if isinstance(f, ElementOf) and isinstance(f.set_expr, Union):
            if isinstance(f.set_expr.left, Complement):
                candidates.append(ElementOf(f.element, f.set_expr.left.operand))
            if isinstance(f.set_expr.right, Complement):
                candidates.append(ElementOf(f.element, f.set_expr.right.operand))

        deduped: List[ASTNode] = []
        seen = set()
        for candidate in candidates:
            sig = str(candidate)
            if isinstance(candidate, ElementOf):
                opposite_sig = str(NotElementOf(candidate.element, candidate.set_expr))
            elif isinstance(candidate, NotElementOf):
                opposite_sig = str(ElementOf(candidate.element, candidate.set_expr))
            else:
                opposite_sig = str(Not(candidate))
            if sig in seen:
                continue
            if sig in assumption_strs or opposite_sig in assumption_strs:
                continue
            seen.add(sig)
            deduped.append(candidate)
        return deduped

    def _dedupe_all_goal_assumptions(self):
        """Normalize assumptions after each rule application."""
        for g in self.state.goals.values():
            g.assumptions = self.state.dedupe_assumptions(g.assumptions)

    def export_json(self) -> dict:
        """Export the proof as JSON."""
        return self.state.to_export_json()

    def export_latex(self) -> str:
        """Export the proof as LaTeX."""
        return self.state.to_latex()

    def get_state(self) -> dict:
        """Get the current proof state."""
        return self.state.to_dict()

    def get_graph_data(self) -> dict:
        """Get proof state formatted for Cytoscape.js visualization."""
        nodes = []
        edges = []

        for gid, goal in self.state.goals.items():
            node_class = "proven" if goal.is_proven else "open"
            if gid == self.state.main_goal:
                node_class += " main"
            nodes.append({
                "data": {
                    "id": gid,
                    "label": str(goal.formula),
                    "is_proven": goal.is_proven,
                    "rule": goal.rule_applied or "",
                    "goal_label": goal.label,
                },
                "classes": node_class,
            })

            if goal.parent_id:
                edges.append({
                    "data": {
                        "id": f"e_{goal.parent_id}_{gid}",
                        "source": goal.parent_id,
                        "target": gid,
                        "label": goal.rule_applied or "",
                    }
                })

        return {
            "nodes": nodes,
            "edges": edges,
        }
