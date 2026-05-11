"""
Z3 SMT solver integration for proof checking and hint generation.
Converts AST formulas to Z3 expressions and checks validity/satisfiability.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from parser.ast_nodes import (
    ASTNode, Variable, Constant, And, Or, Not, Implies, Iff,
    Forall, Exists, Equals, NotEquals, Bottom, Top,
    Predicate, ElementOf, NotElementOf, Intersect, Union,
    Complement, Subset, Superset
)

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False


class Z3Solver:
    """Interface to the Z3 SMT solver for validity/satisfiability checks."""

    def __init__(self):
        if not Z3_AVAILABLE:
            raise ImportError("z3-solver package is not installed. Install with: pip install z3-solver")
        self._var_cache: Dict[str, z3.ExprRef] = {}
        self._sort_cache: Dict[str, z3.SortRef] = {}

    def _get_bool_var(self, name: str) -> z3.BoolRef:
        """Get or create a Z3 Boolean variable."""
        if name not in self._var_cache:
            self._var_cache[name] = z3.Bool(name)
        return self._var_cache[name]

    def _get_int_var(self, name: str) -> z3.ArithRef:
        if name not in self._var_cache:
            self._var_cache[name] = z3.Int(name)
        return self._var_cache[name]

    def _reset_cache(self):
        self._var_cache.clear()
        self._sort_cache.clear()

    def ast_to_z3(self, node: ASTNode) -> z3.ExprRef:
        """Convert an AST node to a Z3 expression (best-effort for propositional)."""
        if isinstance(node, Variable):
            return self._get_bool_var(node.name)
        elif isinstance(node, Constant):
            return self._get_bool_var(node.name)
        elif isinstance(node, Bottom):
            return z3.BoolVal(False)
        elif isinstance(node, Top):
            return z3.BoolVal(True)
        elif isinstance(node, And):
            return z3.And(self.ast_to_z3(node.left), self.ast_to_z3(node.right))
        elif isinstance(node, Or):
            return z3.Or(self.ast_to_z3(node.left), self.ast_to_z3(node.right))
        elif isinstance(node, Not):
            return z3.Not(self.ast_to_z3(node.operand))
        elif isinstance(node, Implies):
            return z3.Implies(self.ast_to_z3(node.left), self.ast_to_z3(node.right))
        elif isinstance(node, Iff):
            l = self.ast_to_z3(node.left)
            r = self.ast_to_z3(node.right)
            return l == r
        elif isinstance(node, Equals):
            return self.ast_to_z3(node.left) == self.ast_to_z3(node.right)
        elif isinstance(node, NotEquals):
            return self.ast_to_z3(node.left) != self.ast_to_z3(node.right)
        elif isinstance(node, Predicate):
            return self._get_bool_var(f"{node.name}_{'_'.join(str(a) for a in node.args)}")
        elif isinstance(node, ElementOf):
            return self._get_bool_var(f"{node.element}_in_{node.set_expr}")
        elif isinstance(node, NotElementOf):
            return z3.Not(self._get_bool_var(f"{node.element}_in_{node.set_expr}"))
        elif isinstance(node, Intersect):
            return self._get_bool_var(f"intersect_{node.left}_{node.right}")
        elif isinstance(node, Union):
            return self._get_bool_var(f"union_{node.left}_{node.right}")
        elif isinstance(node, Subset):
            return self._get_bool_var(f"subset_{node.left}_{node.right}")
        else:
            return self._get_bool_var(str(node))

    def check_validity(self, goal: ASTNode, assumptions: List[ASTNode] = None) -> dict:
        """Check if goal follows from assumptions (is valid under assumptions).

        Returns dict with 'valid' (bool), 'model' (counterexample if invalid).
        """
        self._reset_cache()
        try:
            solver = z3.Solver()
            solver.set("timeout", 5000)

            if assumptions:
                for a in assumptions:
                    solver.add(self.ast_to_z3(a))

            solver.add(z3.Not(self.ast_to_z3(goal)))

            result = solver.check()
            if result == z3.unsat:
                return {"valid": True, "message": "Goal is valid (follows from assumptions)."}
            elif result == z3.sat:
                model = solver.model()
                model_str = str(model)
                return {"valid": False, "message": "Goal does not follow from assumptions.", "model": model_str}
            else:
                return {"valid": None, "message": "Solver returned unknown (timeout or complexity limit)."}
        except Exception as e:
            return {"error": str(e)}

    def check_satisfiable(self, formula: ASTNode) -> dict:
        """Check if a formula is satisfiable."""
        self._reset_cache()
        try:
            solver = z3.Solver()
            solver.set("timeout", 5000)
            solver.add(self.ast_to_z3(formula))

            result = solver.check()
            if result == z3.sat:
                model = solver.model()
                return {"satisfiable": True, "model": str(model)}
            elif result == z3.unsat:
                return {"satisfiable": False, "message": "Formula is unsatisfiable."}
            else:
                return {"satisfiable": None, "message": "Unknown."}
        except Exception as e:
            return {"error": str(e)}

    def check_tautology(self, formula: ASTNode) -> dict:
        """Check if a formula is a tautology (valid without assumptions)."""
        return self.check_validity(formula, [])
