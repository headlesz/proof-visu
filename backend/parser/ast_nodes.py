"""
Abstract Syntax Tree node definitions for logical formulas.
Supports propositional logic, predicate logic, set theory, equality, and induction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import json


class ASTNode:
    """Base class for all AST nodes."""

    def to_dict(self) -> dict:
        raise NotImplementedError

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def free_variables(self) -> set:
        raise NotImplementedError

    def substitute(self, var: str, term: 'ASTNode') -> 'ASTNode':
        raise NotImplementedError

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self):
        return hash(self.to_json())


# --- Atomic Formulas ---

@dataclass
class Variable(ASTNode):
    name: str

    def __repr__(self):
        return self.name

    def to_dict(self):
        return {"type": "variable", "name": self.name}

    def free_variables(self):
        return {self.name}

    def substitute(self, var, term):
        if self.name == var:
            return term
        return self

    def to_latex(self):
        return self.name


@dataclass
class Constant(ASTNode):
    name: str

    def __repr__(self):
        return self.name

    def to_dict(self):
        return {"type": "constant", "name": self.name}

    def free_variables(self):
        return set()

    def substitute(self, var, term):
        return self

    def to_latex(self):
        return self.name


@dataclass
class Bottom(ASTNode):
    def __repr__(self):
        return "⊥"

    def to_dict(self):
        return {"type": "bottom"}

    def free_variables(self):
        return set()

    def substitute(self, var, term):
        return self

    def to_latex(self):
        return "\\bot"


@dataclass
class Top(ASTNode):
    def __repr__(self):
        return "⊤"

    def to_dict(self):
        return {"type": "top"}

    def free_variables(self):
        return set()

    def substitute(self, var, term):
        return self

    def to_latex(self):
        return "\\top"


@dataclass
class EmptySet(ASTNode):
    def __repr__(self):
        return "∅"

    def to_dict(self):
        return {"type": "emptyset"}

    def free_variables(self):
        return set()

    def substitute(self, var, term):
        return self

    def to_latex(self):
        return "\\emptyset"


@dataclass
class Zero(ASTNode):
    def __repr__(self):
        return "0"

    def to_dict(self):
        return {"type": "zero"}

    def free_variables(self):
        return set()

    def substitute(self, var, term):
        return self

    def to_latex(self):
        return "0"


# --- Propositional Connectives ---

@dataclass
class And(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ∧ {self.right})"

    def to_dict(self):
        return {"type": "and", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return And(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\land {self.right.to_latex()})"


@dataclass
class Or(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ∨ {self.right})"

    def to_dict(self):
        return {"type": "or", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Or(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\lor {self.right.to_latex()})"


@dataclass
class Not(ASTNode):
    operand: ASTNode

    def __repr__(self):
        return f"¬{self.operand}"

    def to_dict(self):
        return {"type": "not", "operand": self.operand.to_dict()}

    def free_variables(self):
        return self.operand.free_variables()

    def substitute(self, var, term):
        return Not(self.operand.substitute(var, term))

    def to_latex(self):
        return f"\\neg {self.operand.to_latex()}"


@dataclass
class Implies(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} → {self.right})"

    def to_dict(self):
        return {"type": "implies", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Implies(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\rightarrow {self.right.to_latex()})"


@dataclass
class Iff(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ↔ {self.right})"

    def to_dict(self):
        return {"type": "iff", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Iff(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\leftrightarrow {self.right.to_latex()})"


# --- Quantifiers ---

@dataclass
class Forall(ASTNode):
    variable: str
    body: ASTNode

    def __repr__(self):
        return f"∀{self.variable}.{self.body}"

    def to_dict(self):
        return {"type": "forall", "variable": self.variable, "body": self.body.to_dict()}

    def free_variables(self):
        return self.body.free_variables() - {self.variable}

    def substitute(self, var, term):
        if var == self.variable:
            return self
        if self.variable in term.free_variables():
            new_var = self._fresh_var(self.variable, term.free_variables() | self.body.free_variables())
            new_body = self.body.substitute(self.variable, Variable(new_var))
            return Forall(new_var, new_body.substitute(var, term))
        return Forall(self.variable, self.body.substitute(var, term))

    def _fresh_var(self, base, used):
        i = 0
        while f"{base}{i}" in used:
            i += 1
        return f"{base}{i}"

    def to_latex(self):
        return f"\\forall {self.variable}. {self.body.to_latex()}"


@dataclass
class Exists(ASTNode):
    variable: str
    body: ASTNode

    def __repr__(self):
        return f"∃{self.variable}.{self.body}"

    def to_dict(self):
        return {"type": "exists", "variable": self.variable, "body": self.body.to_dict()}

    def free_variables(self):
        return self.body.free_variables() - {self.variable}

    def substitute(self, var, term):
        if var == self.variable:
            return self
        if self.variable in term.free_variables():
            new_var = self._fresh_var(self.variable, term.free_variables() | self.body.free_variables())
            new_body = self.body.substitute(self.variable, Variable(new_var))
            return Exists(new_var, new_body.substitute(var, term))
        return Exists(self.variable, self.body.substitute(var, term))

    def _fresh_var(self, base, used):
        i = 0
        while f"{base}{i}" in used:
            i += 1
        return f"{base}{i}"

    def to_latex(self):
        return f"\\exists {self.variable}. {self.body.to_latex()}"


# --- Predicates and Functions ---

@dataclass
class Predicate(ASTNode):
    name: str
    args: List[ASTNode] = field(default_factory=list)

    def __repr__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    def to_dict(self):
        return {"type": "predicate", "name": self.name, "args": [a.to_dict() for a in self.args]}

    def free_variables(self):
        result = set()
        for a in self.args:
            result |= a.free_variables()
        return result

    def substitute(self, var, term):
        return Predicate(self.name, [a.substitute(var, term) for a in self.args])

    def to_latex(self):
        args_str = ", ".join(a.to_latex() for a in self.args)
        return f"{self.name}({args_str})"


@dataclass
class FunctionApp(ASTNode):
    name: str
    args: List[ASTNode] = field(default_factory=list)

    def __repr__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    def to_dict(self):
        return {"type": "function", "name": self.name, "args": [a.to_dict() for a in self.args]}

    def free_variables(self):
        result = set()
        for a in self.args:
            result |= a.free_variables()
        return result

    def substitute(self, var, term):
        return FunctionApp(self.name, [a.substitute(var, term) for a in self.args])

    def to_latex(self):
        args_str = ", ".join(a.to_latex() for a in self.args)
        return f"{self.name}({args_str})"


# --- Equality ---

@dataclass
class Equals(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} = {self.right})"

    def to_dict(self):
        return {"type": "equals", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Equals(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} = {self.right.to_latex()})"


@dataclass
class NotEquals(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ≠ {self.right})"

    def to_dict(self):
        return {"type": "not_equals", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return NotEquals(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\neq {self.right.to_latex()})"


# --- Set Theory ---

@dataclass
class Union(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ∪ {self.right})"

    def to_dict(self):
        return {"type": "union", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Union(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\cup {self.right.to_latex()})"


@dataclass
class Intersect(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ∩ {self.right})"

    def to_dict(self):
        return {"type": "intersect", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Intersect(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\cap {self.right.to_latex()})"


@dataclass
class Complement(ASTNode):
    operand: ASTNode

    def __repr__(self):
        return f"{self.operand}ᶜ"

    def to_dict(self):
        return {"type": "complement", "operand": self.operand.to_dict()}

    def free_variables(self):
        return self.operand.free_variables()

    def substitute(self, var, term):
        return Complement(self.operand.substitute(var, term))

    def to_latex(self):
        return f"{self.operand.to_latex()}^c"


@dataclass
class ElementOf(ASTNode):
    element: ASTNode
    set_expr: ASTNode

    def __repr__(self):
        return f"({self.element} ∈ {self.set_expr})"

    def to_dict(self):
        return {"type": "element_of", "element": self.element.to_dict(), "set": self.set_expr.to_dict()}

    def free_variables(self):
        return self.element.free_variables() | self.set_expr.free_variables()

    def substitute(self, var, term):
        return ElementOf(self.element.substitute(var, term), self.set_expr.substitute(var, term))

    def to_latex(self):
        return f"({self.element.to_latex()} \\in {self.set_expr.to_latex()})"


@dataclass
class NotElementOf(ASTNode):
    element: ASTNode
    set_expr: ASTNode

    def __repr__(self):
        return f"({self.element} ∉ {self.set_expr})"

    def to_dict(self):
        return {"type": "not_element_of", "element": self.element.to_dict(), "set": self.set_expr.to_dict()}

    def free_variables(self):
        return self.element.free_variables() | self.set_expr.free_variables()

    def substitute(self, var, term):
        return NotElementOf(self.element.substitute(var, term), self.set_expr.substitute(var, term))

    def to_latex(self):
        return f"({self.element.to_latex()} \\notin {self.set_expr.to_latex()})"


@dataclass
class Subset(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ⊆ {self.right})"

    def to_dict(self):
        return {"type": "subset", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Subset(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\subseteq {self.right.to_latex()})"


@dataclass
class Superset(ASTNode):
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        return f"({self.left} ⊇ {self.right})"

    def to_dict(self):
        return {"type": "superset", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def substitute(self, var, term):
        return Superset(self.left.substitute(var, term), self.right.substitute(var, term))

    def to_latex(self):
        return f"({self.left.to_latex()} \\supseteq {self.right.to_latex()})"


# --- Induction (Peano) ---

@dataclass
class Successor(ASTNode):
    operand: ASTNode

    def __repr__(self):
        return f"s({self.operand})"

    def to_dict(self):
        return {"type": "successor", "operand": self.operand.to_dict()}

    def free_variables(self):
        return self.operand.free_variables()

    def substitute(self, var, term):
        return Successor(self.operand.substitute(var, term))

    def to_latex(self):
        return f"s({self.operand.to_latex()})"


def ast_from_dict(d: dict) -> ASTNode:
    """Reconstruct an AST node from a dictionary."""
    t = d["type"]
    if t == "variable":
        return Variable(d["name"])
    elif t == "constant":
        return Constant(d["name"])
    elif t == "bottom":
        return Bottom()
    elif t == "top":
        return Top()
    elif t == "emptyset":
        return EmptySet()
    elif t == "zero":
        return Zero()
    elif t == "and":
        return And(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "or":
        return Or(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "not":
        return Not(ast_from_dict(d["operand"]))
    elif t == "implies":
        return Implies(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "iff":
        return Iff(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "forall":
        return Forall(d["variable"], ast_from_dict(d["body"]))
    elif t == "exists":
        return Exists(d["variable"], ast_from_dict(d["body"]))
    elif t == "predicate":
        return Predicate(d["name"], [ast_from_dict(a) for a in d["args"]])
    elif t == "function":
        return FunctionApp(d["name"], [ast_from_dict(a) for a in d["args"]])
    elif t == "equals":
        return Equals(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "not_equals":
        return NotEquals(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "union":
        return Union(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "intersect":
        return Intersect(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "complement":
        return Complement(ast_from_dict(d["operand"]))
    elif t == "element_of":
        return ElementOf(ast_from_dict(d["element"]), ast_from_dict(d["set"]))
    elif t == "not_element_of":
        return NotElementOf(ast_from_dict(d["element"]), ast_from_dict(d["set"]))
    elif t == "subset":
        return Subset(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "superset":
        return Superset(ast_from_dict(d["left"]), ast_from_dict(d["right"]))
    elif t == "successor":
        return Successor(ast_from_dict(d["operand"]))
    else:
        raise ValueError(f"Unknown AST node type: {t}")
