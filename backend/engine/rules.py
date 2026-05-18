"""
Inference rule implementations for natural deduction.
Each rule takes the proof state + goal and produces new subgoals.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from parser.ast_nodes import (
    ASTNode, And, Or, Not, Implies, Iff, Forall, Exists,
    Equals, NotEquals, Union, Intersect, Complement,
    ElementOf, NotElementOf, Subset, Superset,
    Variable, Constant, Bottom, Top, EmptySet, Predicate, Successor, Zero
)
from .proof_state import ProofState, GoalNode


class RuleError(Exception):
    """Raised when a rule cannot be applied."""
    pass


class InferenceRule:
    """Base class for inference rules."""
    name: str = ""
    description: str = ""
    category: str = "general"

    def is_applicable(self, state: ProofState, goal: GoalNode, params: Dict = None) -> bool:
        raise NotImplementedError

    def apply(self, state: ProofState, goal: GoalNode, params: Dict = None) -> List[str]:
        """Apply the rule. Returns list of new goal IDs created."""
        raise NotImplementedError

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
        }


# === Propositional Rules ===

class AndIntro(InferenceRule):
    name = "and_intro"
    description = "∧-Introduction: To prove A ∧ B, prove A and prove B separately."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, And)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, And):
            raise RuleError("Goal is not a conjunction")
        state.save_checkpoint()
        g1 = state.add_goal(goal.formula.left, list(goal.assumptions), goal.id, "Prove left conjunct")
        g2 = state.add_goal(goal.formula.right, list(goal.assumptions), goal.id, "Prove right conjunct")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       f"Split {goal.formula} into {goal.formula.left} and {goal.formula.right}")
        return [g1.id, g2.id]


class AndElimLeft(InferenceRule):
    name = "and_elim_left"
    description = "∧-Elimination (Left): From A ∧ B in assumptions, derive A."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, And) for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, And):
                    source = a
                    break
        if not source or not isinstance(source, And):
            raise RuleError("No conjunction found in assumptions")
        state.save_checkpoint()
        new_assumptions = list(goal.assumptions) + [source.left]
        goal.assumptions = new_assumptions
        state.add_step(self.name, goal.id, [], source.left,
                       note=f"From {source}, derive {source.left}")
        return []


class AndElimRight(InferenceRule):
    name = "and_elim_right"
    description = "∧-Elimination (Right): From A ∧ B in assumptions, derive B."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, And) for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, And):
                    source = a
                    break
        if not source or not isinstance(source, And):
            raise RuleError("No conjunction found in assumptions")
        state.save_checkpoint()
        new_assumptions = list(goal.assumptions) + [source.right]
        goal.assumptions = new_assumptions
        state.add_step(self.name, goal.id, [], source.right,
                       note=f"From {source}, derive {source.right}")
        return []


class OrIntroLeft(InferenceRule):
    name = "or_intro_left"
    description = "∨-Introduction (Left): From goal A, prove A ∨ B by proving A."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Or)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Or):
            raise RuleError("Goal is not a disjunction")
        state.save_checkpoint()
        g = state.add_goal(goal.formula.left, list(goal.assumptions), goal.id, "Prove left disjunct")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Prove {goal.formula} by proving {goal.formula.left}")
        return [g.id]


class OrIntroRight(InferenceRule):
    name = "or_intro_right"
    description = "∨-Introduction (Right): From goal A ∨ B, prove B."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Or)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Or):
            raise RuleError("Goal is not a disjunction")
        state.save_checkpoint()
        g = state.add_goal(goal.formula.right, list(goal.assumptions), goal.id, "Prove right disjunct")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Prove {goal.formula} by proving {goal.formula.right}")
        return [g.id]


class OrElim(InferenceRule):
    name = "or_elim"
    description = "∨-Elimination: From A ∨ B in assumptions, prove goal from A and from B (case split)."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, Or) for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, Or):
                    source = a
                    break
        if not source or not isinstance(source, Or):
            raise RuleError("No disjunction found in assumptions")
        state.save_checkpoint()
        assumptions_without = [a for a in goal.assumptions if a != source]
        g1 = state.add_goal(goal.formula, assumptions_without + [source.left], goal.id, f"Case: {source.left}")
        g2 = state.add_goal(goal.formula, assumptions_without + [source.right], goal.id, f"Case: {source.right}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       f"Case split on {source}")
        return [g1.id, g2.id]


class ImpliesIntro(InferenceRule):
    name = "implies_intro"
    description = "→-Introduction: To prove A → B, assume A and prove B."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Implies)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Implies):
            raise RuleError("Goal is not an implication")
        state.save_checkpoint()
        new_assumptions = list(goal.assumptions) + [goal.formula.left]
        g = state.add_goal(goal.formula.right, new_assumptions, goal.id,
                           f"Assume {goal.formula.left}, prove {goal.formula.right}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Assume {goal.formula.left}")
        return [g.id]


class ImpliesElim(InferenceRule):
    name = "implies_elim"
    description = "→-Elimination (Modus Ponens): From A and A → B, derive B."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        for a in goal.assumptions:
            if isinstance(a, Implies) and a.right == goal.formula:
                return True
            if isinstance(a, Implies):
                for b in goal.assumptions:
                    if b == a.left:
                        return True
        return False

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        imp = None
        if source_idx is not None:
            imp = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, Implies) and a.right == goal.formula:
                    imp = a
                    break
            if not imp:
                for a in goal.assumptions:
                    if (
                        isinstance(a, Implies)
                        and any(existing == a.left for existing in goal.assumptions)
                        and not any(existing == a.right for existing in goal.assumptions)
                    ):
                        imp = a
                        break
        if not imp or not isinstance(imp, Implies):
            raise RuleError("No suitable implication found")

        state.save_checkpoint()
        if imp.right == goal.formula:
            g = state.add_goal(imp.left, list(goal.assumptions), goal.id,
                               f"Prove antecedent {imp.left} for modus ponens")
            state.mark_proven(goal.id, self.name)
            state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                           f"Modus ponens: need {imp.left} to get {imp.right}")
            return [g.id]
        else:
            has_antecedent = any(a == imp.left for a in goal.assumptions)
            if has_antecedent:
                goal.assumptions = list(goal.assumptions) + [imp.right]
                state.add_step(self.name, goal.id, [], imp.right,
                               note=f"Modus ponens: from {imp.left} and {imp}, derive {imp.right}")
                return []
            else:
                raise RuleError("Cannot apply modus ponens: antecedent not available")


class NotIntro(InferenceRule):
    name = "not_intro"
    description = "¬-Introduction: To prove ¬A, assume A and derive ⊥ (contradiction)."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Not)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Not):
            raise RuleError("Goal is not a negation")
        state.save_checkpoint()
        new_assumptions = list(goal.assumptions) + [goal.formula.operand]
        g = state.add_goal(Bottom(), new_assumptions, goal.id,
                           f"Assume {goal.formula.operand}, derive contradiction")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Assume {goal.formula.operand} for contradiction")
        return [g.id]


class NotElim(InferenceRule):
    name = "not_elim"
    description = "¬-Elimination (Double Negation): From ¬¬A, derive A."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        for a in goal.assumptions:
            if isinstance(a, Not) and isinstance(a.operand, Not) and a.operand.operand == goal.formula:
                return True
        return False

    def apply(self, state, goal, params=None):
        for a in goal.assumptions:
            if isinstance(a, Not) and isinstance(a.operand, Not) and a.operand.operand == goal.formula:
                state.save_checkpoint()
                state.mark_proven(goal.id, self.name)
                state.add_step(self.name, goal.id, [], goal.formula,
                               note=f"Double negation elimination: ¬¬{goal.formula} → {goal.formula}")
                return []
        raise RuleError("No double negation of goal found in assumptions")


class IffIntro(InferenceRule):
    name = "iff_intro"
    description = "↔-Introduction: To prove A ↔ B, prove A → B and B → A."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Iff)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Iff):
            raise RuleError("Goal is not a biconditional")
        state.save_checkpoint()
        g1 = state.add_goal(Implies(goal.formula.left, goal.formula.right),
                            list(goal.assumptions), goal.id, "Forward direction")
        g2 = state.add_goal(Implies(goal.formula.right, goal.formula.left),
                            list(goal.assumptions), goal.id, "Backward direction")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       "Split biconditional into two implications")
        return [g1.id, g2.id]


class Assumption(InferenceRule):
    name = "assumption"
    description = "Close goal using a matching assumption."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        return any(a == goal.formula for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        if not any(a == goal.formula for a in goal.assumptions):
            raise RuleError("Goal formula not found in assumptions")
        state.save_checkpoint()
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula,
                       note=f"Goal {goal.formula} matches an assumption")
        return []


class Contradiction(InferenceRule):
    name = "contradiction"
    description = "If both A and ¬A are in assumptions, derive ⊥ (or any goal)."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        for a in goal.assumptions:
            neg = Not(a)
            if neg in goal.assumptions:
                return True
            if isinstance(a, Not) and a.operand in goal.assumptions:
                return True
            if isinstance(a, ElementOf):
                if NotElementOf(a.element, a.set_expr) in goal.assumptions:
                    return True
            if isinstance(a, NotElementOf):
                if ElementOf(a.element, a.set_expr) in goal.assumptions:
                    return True
                if isinstance(a.set_expr, Union):
                    if ElementOf(a.element, a.set_expr.left) in goal.assumptions:
                        return True
                    if ElementOf(a.element, a.set_expr.right) in goal.assumptions:
                        return True
                if isinstance(a.set_expr, Intersect):
                    left = ElementOf(a.element, a.set_expr.left)
                    right = ElementOf(a.element, a.set_expr.right)
                    if left in goal.assumptions and right in goal.assumptions:
                        return True
        return False

    def apply(self, state, goal, params=None):
        for a in goal.assumptions:
            if Not(a) in goal.assumptions:
                state.save_checkpoint()
                state.mark_proven(goal.id, self.name)
                state.add_step(self.name, goal.id, [], goal.formula,
                               note=f"Contradiction: {a} and ¬{a}")
                return []
            if isinstance(a, Not) and a.operand in goal.assumptions:
                state.save_checkpoint()
                state.mark_proven(goal.id, self.name)
                state.add_step(self.name, goal.id, [], goal.formula,
                               note=f"Contradiction: {a.operand} and {a}")
                return []
            if isinstance(a, ElementOf) and NotElementOf(a.element, a.set_expr) in goal.assumptions:
                state.save_checkpoint()
                state.mark_proven(goal.id, self.name)
                state.add_step(self.name, goal.id, [], goal.formula,
                               note=f"Contradiction: {a} and {NotElementOf(a.element, a.set_expr)}")
                return []
            if isinstance(a, NotElementOf) and ElementOf(a.element, a.set_expr) in goal.assumptions:
                state.save_checkpoint()
                state.mark_proven(goal.id, self.name)
                state.add_step(self.name, goal.id, [], goal.formula,
                               note=f"Contradiction: {ElementOf(a.element, a.set_expr)} and {a}")
                return []
            if isinstance(a, NotElementOf) and isinstance(a.set_expr, Union):
                left = ElementOf(a.element, a.set_expr.left)
                right = ElementOf(a.element, a.set_expr.right)
                if left in goal.assumptions:
                    state.save_checkpoint()
                    state.mark_proven(goal.id, self.name)
                    state.add_step(self.name, goal.id, [], goal.formula,
                                   note=f"Contradiction: {left} implies membership in {a.set_expr}, but {a}")
                    return []
                if right in goal.assumptions:
                    state.save_checkpoint()
                    state.mark_proven(goal.id, self.name)
                    state.add_step(self.name, goal.id, [], goal.formula,
                                   note=f"Contradiction: {right} implies membership in {a.set_expr}, but {a}")
                    return []
            if isinstance(a, NotElementOf) and isinstance(a.set_expr, Intersect):
                left = ElementOf(a.element, a.set_expr.left)
                right = ElementOf(a.element, a.set_expr.right)
                if left in goal.assumptions and right in goal.assumptions:
                    state.save_checkpoint()
                    state.mark_proven(goal.id, self.name)
                    state.add_step(self.name, goal.id, [], goal.formula,
                                   note=f"Contradiction: {left} and {right} imply membership in {a.set_expr}, but {a}")
                    return []
        raise RuleError("No contradiction found in assumptions")


class ClassicalCases(InferenceRule):
    name = "classical_cases"
    description = "Classical case split: To prove a goal, prove it assuming A and assuming ¬A."
    category = "propositional"

    def is_applicable(self, state, goal, params=None):
        p = params or {}
        return bool(p.get("formula") or p.get("case_formula"))

    def apply(self, state, goal, params=None):
        p = params or {}
        formula_param = p.get("formula") or p.get("case_formula")
        if not formula_param:
            raise RuleError("classical_cases requires a formula parameter")

        if isinstance(formula_param, ASTNode):
            case_formula = formula_param
        else:
            from parser import FormulaParser
            parser = FormulaParser()
            case_formula = parser.parse(str(formula_param))

        if isinstance(case_formula, ElementOf):
            opposite = NotElementOf(case_formula.element, case_formula.set_expr)
        elif isinstance(case_formula, NotElementOf):
            opposite = ElementOf(case_formula.element, case_formula.set_expr)
        else:
            opposite = Not(case_formula)

        state.save_checkpoint()
        g1 = state.add_goal(goal.formula, list(goal.assumptions) + [case_formula],
                            goal.id, f"Case: {case_formula}")
        g2 = state.add_goal(goal.formula, list(goal.assumptions) + [opposite],
                            goal.id, f"Case: {opposite}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       f"Classical case split on {case_formula}",
                       params={"formula": str(case_formula)})
        return [g1.id, g2.id]


# === Quantifier Rules ===

class ForallIntro(InferenceRule):
    name = "forall_intro"
    description = "∀-Introduction: To prove ∀x.P(x), prove P(x) for arbitrary fresh x."
    category = "quantifier"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Forall)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Forall):
            raise RuleError("Goal is not a universal quantification")
        state.save_checkpoint()
        var = goal.formula.variable
        assumption_fvs = set()
        for a in goal.assumptions:
            assumption_fvs |= a.free_variables()
        if var in assumption_fvs:
            fresh = state.fresh_variable(var)
            body = goal.formula.body.substitute(var, Variable(fresh))
        else:
            fresh = var
            body = goal.formula.body
        g = state.add_goal(body, list(goal.assumptions), goal.id,
                           f"Prove for arbitrary {fresh}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Introduce universal variable {fresh}",
                       params={"variable": fresh})
        return [g.id]


class ForallElim(InferenceRule):
    name = "forall_elim"
    description = "∀-Elimination: From ∀x.P(x), instantiate with a specific term."
    category = "quantifier"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, Forall) for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        p = params or {}
        source_idx = p.get("source_idx", None)
        term_str = p.get("term", None)

        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, Forall):
                    source = a
                    break
        if not source or not isinstance(source, Forall):
            raise RuleError("No universal quantification found")

        if term_str:
            from parser import FormulaParser
            parser = FormulaParser()
            term = parser.parse(term_str)
        else:
            term = Variable(source.variable)

        state.save_checkpoint()
        instantiated = source.body.substitute(source.variable, term)
        goal.assumptions = list(goal.assumptions) + [instantiated]
        state.add_step(self.name, goal.id, [], instantiated,
                       note=f"Instantiate {source} with {term}",
                       params={"term": str(term)})
        return []


class ExistsIntro(InferenceRule):
    name = "exists_intro"
    description = "∃-Introduction: To prove ∃x.P(x), provide a witness term t and prove P(t)."
    category = "quantifier"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Exists)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Exists):
            raise RuleError("Goal is not an existential quantification")
        p = params or {}
        term_str = p.get("term", None)

        if term_str:
            from parser import FormulaParser
            parser = FormulaParser()
            term = parser.parse(term_str)
        else:
            term = Variable(goal.formula.variable)

        state.save_checkpoint()
        witness_body = goal.formula.body.substitute(goal.formula.variable, term)
        g = state.add_goal(witness_body, list(goal.assumptions), goal.id,
                           f"Prove with witness {term}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Existential introduction with witness {term}",
                       params={"term": str(term)})
        return [g.id]


class ExistsElim(InferenceRule):
    name = "exists_elim"
    description = "∃-Elimination: From ∃x.P(x), assume P(c) for fresh c and prove goal."
    category = "quantifier"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, Exists) for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        p = params or {}
        source_idx = p.get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, Exists):
                    source = a
                    break
        if not source or not isinstance(source, Exists):
            raise RuleError("No existential quantification found")

        state.save_checkpoint()
        fresh = state.fresh_variable(source.variable)
        witness_assumption = source.body.substitute(source.variable, Variable(fresh))
        new_assumptions = [a for a in goal.assumptions if a != source] + [witness_assumption]
        g = state.add_goal(goal.formula, new_assumptions, goal.id,
                           f"With fresh witness {fresh}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Existential elimination: assume {witness_assumption}",
                       params={"fresh_var": fresh})
        return [g.id]


# === Set Theory Rules ===

class IntersectIntro(InferenceRule):
    name = "intersect_intro"
    description = "∩-Introduction: To prove x ∈ A ∩ B, prove x ∈ A and x ∈ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, ElementOf) and isinstance(goal.formula.set_expr, Intersect)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not (isinstance(f, ElementOf) and isinstance(f.set_expr, Intersect)):
            raise RuleError("Goal is not of the form x ∈ A ∩ B")
        state.save_checkpoint()
        g1 = state.add_goal(ElementOf(f.element, f.set_expr.left),
                            list(goal.assumptions), goal.id, f"Prove {f.element} ∈ {f.set_expr.left}")
        g2 = state.add_goal(ElementOf(f.element, f.set_expr.right),
                            list(goal.assumptions), goal.id, f"Prove {f.element} ∈ {f.set_expr.right}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g1.id, g2.id],
                       f"Split intersection into membership of both sets")
        return [g1.id, g2.id]


class IntersectElim(InferenceRule):
    name = "intersect_elim"
    description = "∩-Elimination: From x ∈ A ∩ B, derive x ∈ A and x ∈ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        assumption_strs = {str(a) for a in goal.assumptions}
        for a in goal.assumptions:
            if isinstance(a, ElementOf) and isinstance(a.set_expr, Intersect):
                left = str(ElementOf(a.element, a.set_expr.left))
                right = str(ElementOf(a.element, a.set_expr.right))
                if left not in assumption_strs or right not in assumption_strs:
                    return True
        return False

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, ElementOf) and isinstance(a.set_expr, Intersect):
                    source = a
                    break
        if not source:
            raise RuleError("No intersection membership found")
        state.save_checkpoint()
        left = ElementOf(source.element, source.set_expr.left)
        right = ElementOf(source.element, source.set_expr.right)
        goal.assumptions = list(goal.assumptions) + [left, right]
        state.add_step(self.name, goal.id, [], source,
                       note=f"From {source}, derive {left} and {right}")
        return []


class UnionIntroLeft(InferenceRule):
    name = "union_intro_left"
    description = "∪-Introduction (Left): From x ∈ A, derive x ∈ A ∪ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, ElementOf) and isinstance(goal.formula.set_expr, Union)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not (isinstance(f, ElementOf) and isinstance(f.set_expr, Union)):
            raise RuleError("Goal is not of the form x ∈ A ∪ B")
        state.save_checkpoint()
        g = state.add_goal(ElementOf(f.element, f.set_expr.left),
                           list(goal.assumptions), goal.id, f"Prove {f.element} ∈ {f.set_expr.left}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g.id],
                       f"Prove union membership via left set")
        return [g.id]


class UnionIntroRight(InferenceRule):
    name = "union_intro_right"
    description = "∪-Introduction (Right): From x ∈ B, derive x ∈ A ∪ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, ElementOf) and isinstance(goal.formula.set_expr, Union)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not (isinstance(f, ElementOf) and isinstance(f.set_expr, Union)):
            raise RuleError("Goal is not of the form x ∈ A ∪ B")
        state.save_checkpoint()
        g = state.add_goal(ElementOf(f.element, f.set_expr.right),
                           list(goal.assumptions), goal.id, f"Prove {f.element} ∈ {f.set_expr.right}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g.id],
                       f"Prove union membership via right set")
        return [g.id]


class UnionElim(InferenceRule):
    name = "union_elim"
    description = "∪-Elimination: From x ∈ A ∪ B, do case split: x ∈ A or x ∈ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        assumption_strs = {str(a) for a in goal.assumptions}
        for a in goal.assumptions:
            if isinstance(a, ElementOf) and isinstance(a.set_expr, Union):
                left = str(ElementOf(a.element, a.set_expr.left))
                right = str(ElementOf(a.element, a.set_expr.right))
                # Only offer if both parts aren't already known
                if left not in assumption_strs or right not in assumption_strs:
                    return True
        return False

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, ElementOf) and isinstance(a.set_expr, Union):
                    source = a
                    break
        if not source:
            raise RuleError("No union membership found")
        state.save_checkpoint()
        assumptions_without = [a for a in goal.assumptions if a != source]
        left_mem = ElementOf(source.element, source.set_expr.left)
        right_mem = ElementOf(source.element, source.set_expr.right)
        g1 = state.add_goal(goal.formula, assumptions_without + [left_mem], goal.id,
                            f"Case: {left_mem}")
        g2 = state.add_goal(goal.formula, assumptions_without + [right_mem], goal.id,
                            f"Case: {right_mem}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       f"Case split on {source}")
        return [g1.id, g2.id]


class ComplementIntro(InferenceRule):
    name = "complement_intro"
    description = "Complement Introduction: To prove x ∈ Aᶜ, prove x ∉ A."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, ElementOf) and isinstance(goal.formula.set_expr, Complement)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not (isinstance(f, ElementOf) and isinstance(f.set_expr, Complement)):
            raise RuleError("Goal is not of the form x ∈ Aᶜ")
        state.save_checkpoint()
        target = NotElementOf(f.element, f.set_expr.operand)
        g = state.add_goal(target, list(goal.assumptions), goal.id,
                           f"Prove {f.element} ∉ {f.set_expr.operand}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g.id],
                       f"Use complement definition: prove {target}")
        return [g.id]


class ComplementElim(InferenceRule):
    name = "complement_elim"
    description = "Complement Elimination: From x ∈ Aᶜ, derive x ∉ A."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        assumption_strs = {str(a) for a in goal.assumptions}
        for a in goal.assumptions:
            if isinstance(a, ElementOf) and isinstance(a.set_expr, Complement):
                derived = str(NotElementOf(a.element, a.set_expr.operand))
                if derived not in assumption_strs:
                    return True
        return False

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        assumption_strs = {str(a) for a in goal.assumptions}
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, ElementOf) and isinstance(a.set_expr, Complement):
                    derived = str(NotElementOf(a.element, a.set_expr.operand))
                    if derived not in assumption_strs:
                        source = a
                        break
        if not (source and isinstance(source, ElementOf) and isinstance(source.set_expr, Complement)):
            raise RuleError("No complement membership found")
        state.save_checkpoint()
        derived = NotElementOf(source.element, source.set_expr.operand)
        goal.assumptions = list(goal.assumptions) + [derived]
        state.add_step(self.name, goal.id, [], derived,
                       note=f"From {source}, derive {derived}")
        return []


class NotComplementIntro(InferenceRule):
    name = "not_complement_intro"
    description = "Complement Nonmembership: To prove x ∉ Aᶜ, prove x ∈ A."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, NotElementOf) and isinstance(goal.formula.set_expr, Complement)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not (isinstance(f, NotElementOf) and isinstance(f.set_expr, Complement)):
            raise RuleError("Goal is not of the form x ∉ Aᶜ")
        state.save_checkpoint()
        target = ElementOf(f.element, f.set_expr.operand)
        g = state.add_goal(target, list(goal.assumptions), goal.id,
                           f"Prove {f.element} ∈ {f.set_expr.operand}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g.id],
                       f"Use complement definition: prove {target}")
        return [g.id]


class NotComplementElim(InferenceRule):
    name = "not_complement_elim"
    description = "Complement Nonmembership Elimination: From x ∉ Aᶜ, derive x ∈ A."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        assumption_strs = {str(a) for a in goal.assumptions}
        for a in goal.assumptions:
            if isinstance(a, NotElementOf) and isinstance(a.set_expr, Complement):
                derived = str(ElementOf(a.element, a.set_expr.operand))
                if derived not in assumption_strs:
                    return True
        return False

    def apply(self, state, goal, params=None):
        source_idx = (params or {}).get("source_idx", None)
        source = None
        assumption_strs = {str(a) for a in goal.assumptions}
        if source_idx is not None:
            source = goal.assumptions[source_idx]
        else:
            for a in goal.assumptions:
                if isinstance(a, NotElementOf) and isinstance(a.set_expr, Complement):
                    derived = str(ElementOf(a.element, a.set_expr.operand))
                    if derived not in assumption_strs:
                        source = a
                        break
        if not (source and isinstance(source, NotElementOf) and isinstance(source.set_expr, Complement)):
            raise RuleError("No complement nonmembership found")
        state.save_checkpoint()
        derived = ElementOf(source.element, source.set_expr.operand)
        goal.assumptions = list(goal.assumptions) + [derived]
        state.add_step(self.name, goal.id, [], derived,
                       note=f"From {source}, derive {derived}")
        return []


class NotElementIntro(InferenceRule):
    name = "not_element_intro"
    description = "∉-Introduction: To prove x ∉ A, assume x ∈ A and derive contradiction."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, NotElementOf)

    def apply(self, state, goal, params=None):
        f = goal.formula
        if not isinstance(f, NotElementOf):
            raise RuleError("Goal is not a nonmembership statement")
        state.save_checkpoint()
        assumption = ElementOf(f.element, f.set_expr)
        g = state.add_goal(Bottom(), list(goal.assumptions) + [assumption],
                           goal.id, f"Assume {assumption}, derive contradiction")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], f, [g.id],
                       f"Assume {assumption} for contradiction")
        return [g.id]


class EmptySetElim(InferenceRule):
    name = "emptyset_elim"
    description = "Empty Set Elimination: From x ∈ ∅, derive any goal."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return any(isinstance(a, ElementOf) and isinstance(a.set_expr, EmptySet)
                   for a in goal.assumptions)

    def apply(self, state, goal, params=None):
        source = None
        for a in goal.assumptions:
            if isinstance(a, ElementOf) and isinstance(a.set_expr, EmptySet):
                source = a
                break
        if not source:
            raise RuleError("No empty-set membership found")
        state.save_checkpoint()
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula,
                       note=f"Empty-set elimination from {source}")
        return []


class SubsetIntro(InferenceRule):
    name = "subset_intro"
    description = "⊆-Introduction: To prove A ⊆ B, assume x ∈ A and prove x ∈ B."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Subset)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Subset):
            raise RuleError("Goal is not a subset relation")
        state.save_checkpoint()
        fresh = state.fresh_variable("x")
        x = Variable(fresh)
        assumption = ElementOf(x, goal.formula.left)
        target = ElementOf(x, goal.formula.right)
        g = state.add_goal(target, list(goal.assumptions) + [assumption], goal.id,
                           f"For arbitrary {fresh} ∈ {goal.formula.left}, prove {fresh} ∈ {goal.formula.right}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g.id],
                       f"Assume {fresh} ∈ {goal.formula.left}",
                       params={"variable": fresh})
        return [g.id]


class EqualityIntro(InferenceRule):
    name = "equality_intro"
    description = "Set Equality: To prove A = B, prove A ⊆ B and B ⊆ A."
    category = "set_theory"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Equals)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Equals):
            raise RuleError("Goal is not an equality")
        state.save_checkpoint()
        g1 = state.add_goal(Subset(goal.formula.left, goal.formula.right),
                            list(goal.assumptions), goal.id,
                            f"Prove {goal.formula.left} ⊆ {goal.formula.right}")
        g2 = state.add_goal(Subset(goal.formula.right, goal.formula.left),
                            list(goal.assumptions), goal.id,
                            f"Prove {goal.formula.right} ⊆ {goal.formula.left}")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       "Prove equality by double inclusion")
        return [g1.id, g2.id]


# === Induction ===

class InductionRule(InferenceRule):
    name = "induction"
    description = "Induction on natural numbers: prove P(0) (base) and P(k)→P(s(k)) (step)."
    category = "induction"

    def is_applicable(self, state, goal, params=None):
        return isinstance(goal.formula, Forall)

    def apply(self, state, goal, params=None):
        if not isinstance(goal.formula, Forall):
            raise RuleError("Goal is not a universal statement for induction")
        state.save_checkpoint()
        var = goal.formula.variable
        body = goal.formula.body

        base_case = body.substitute(var, Zero())
        k_var = state.fresh_variable("k")
        ih = body.substitute(var, Variable(k_var))
        step_goal = body.substitute(var, Successor(Variable(k_var)))

        g1 = state.add_goal(base_case, list(goal.assumptions), goal.id, "Base case: P(0)")
        g2 = state.add_goal(step_goal, list(goal.assumptions) + [ih], goal.id,
                            f"Inductive step: P({k_var}) → P(s({k_var}))")
        state.mark_proven(goal.id, self.name)
        state.add_step(self.name, goal.id, [], goal.formula, [g1.id, g2.id],
                       f"Induction on {var}",
                       params={"variable": var, "ind_var": k_var})
        return [g1.id, g2.id]


# === Registry ===

ALL_RULES = [
    # Propositional
    Assumption(),
    Contradiction(),
    AndIntro(),
    AndElimLeft(),
    AndElimRight(),
    OrIntroLeft(),
    OrIntroRight(),
    OrElim(),
    ImpliesIntro(),
    ImpliesElim(),
    NotIntro(),
    NotElim(),
    IffIntro(),
    ClassicalCases(),
    # Quantifier
    ForallIntro(),
    ForallElim(),
    ExistsIntro(),
    ExistsElim(),
    # Set Theory
    IntersectIntro(),
    IntersectElim(),
    UnionIntroLeft(),
    UnionIntroRight(),
    UnionElim(),
    ComplementIntro(),
    ComplementElim(),
    NotComplementIntro(),
    NotComplementElim(),
    NotElementIntro(),
    EmptySetElim(),
    SubsetIntro(),
    EqualityIntro(),
    # Induction
    InductionRule(),
]

RULES_BY_NAME = {r.name: r for r in ALL_RULES}


def get_applicable_rules(state: ProofState, goal: GoalNode) -> List[InferenceRule]:
    """Return all rules that can be applied to the given goal."""
    if goal.is_proven:
        return []

    # If the goal formula matches an assumption, only offer 'assumption'
    assumption_strs = {str(a) for a in goal.assumptions}
    if str(goal.formula) in assumption_strs:
        return [r for r in ALL_RULES if r.name == 'assumption' and r.is_applicable(state, goal)]

    return [r for r in ALL_RULES if r.is_applicable(state, goal)]
