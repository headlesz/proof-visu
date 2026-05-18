"""
Formula parser using Lark. Converts formula strings into AST nodes.
Supports propositional logic, predicate logic, set theory, equality.
"""
from __future__ import annotations
import os
from lark import Lark, Transformer, v_args, exceptions as lark_exceptions
from .ast_nodes import (
    Variable, Constant, Bottom, Top, EmptySet, Zero,
    And, Or, Not, Implies, Iff,
    Forall, Exists,
    Predicate, FunctionApp,
    Equals, NotEquals,
    Union, Intersect, Complement,
    ElementOf, NotElementOf,
    Subset, Superset,
    Successor, ASTNode
)


class ParseError(Exception):
    """Raised when a formula cannot be parsed."""
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(message)


GRAMMAR = r"""
?start: formula

?formula: biconditional

?biconditional: implication
    | biconditional _IFF implication -> iff_expr

?implication: disjunction
    | disjunction _IMPLIES implication -> implies_expr

?disjunction: conjunction
    | disjunction _OR conjunction -> or_expr

?conjunction: negation
    | conjunction _AND negation -> and_expr

?negation: _NOT negation -> not_expr
    | quantified

?quantified: _FORALL VARIABLE "." formula -> forall_expr
    | _EXISTS VARIABLE "." formula -> exists_expr
    | set_relation

?set_relation: equality
    | set_relation _SUBSET equality -> subset_expr
    | set_relation _SUPERSET equality -> superset_expr
    | set_relation _IN equality -> element_of_expr
    | set_relation _NOTIN equality -> not_element_of_expr

?equality: set_op
    | equality _EQ set_op -> eq_expr
    | equality _NEQ set_op -> neq_expr

?set_op: unary
    | set_op _UNION unary -> union_expr
    | set_op _INTERSECT unary -> intersect_expr

?unary: _COMPLEMENT unary -> complement_expr
    | postfix

?postfix: atom
    | postfix _COMPLEMENT -> complement_expr

?atom: "(" formula ")"
    | _BOTTOM -> bottom
    | _TOP -> top
    | _EMPTYSET -> emptyset
    | _SUCC "(" formula ")" -> successor_expr
    | _ZERO -> zero
    | NAME "(" args ")" -> app_expr
    | NAME -> name_expr

args: formula ("," formula)*

// Tokens - order matters for Lark priority
_FORALL: "∀" | "forall"
_EXISTS: "∃" | "exists"
_AND: "∧" | "&&" | "and"
_OR: "∨" | "||" | "or"
_NOT: "¬" | "~" | "not"
_IMPLIES: "→" | "->" | "=>"
_IFF: "↔" | "<->" | "<=>"
_IN: "∈" | "in"
_NOTIN: "∉" | "notin"
_SUBSET: "⊆" | "subset"
_SUPERSET: "⊇" | "superset"
_UNION: "∪" | "union"
_INTERSECT: "∩" | "cap"
_COMPLEMENT: "ᶜ" | "comp"
_EQ: "="
_NEQ: "!=" | "≠"
_BOTTOM: "⊥" | "false"
_TOP: "⊤" | "true"
_EMPTYSET: "∅" | "emptyset"
_SUCC: "succ"
_ZERO.2: "0"

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
VARIABLE: /[a-z][a-zA-Z0-9_]*/

%import common.WS
%ignore WS
"""


@v_args(inline=True)
class FormulaTransformer(Transformer):
    """Transform Lark parse tree into AST nodes."""

    def and_expr(self, left, right):
        return And(left, right)

    def or_expr(self, left, right):
        return Or(left, right)

    def not_expr(self, operand):
        return Not(operand)

    def implies_expr(self, left, right):
        return Implies(left, right)

    def iff_expr(self, left, right):
        return Iff(left, right)

    def forall_expr(self, var, body):
        return Forall(str(var), body)

    def exists_expr(self, var, body):
        return Exists(str(var), body)

    def eq_expr(self, left, right):
        return Equals(left, right)

    def neq_expr(self, left, right):
        return NotEquals(left, right)

    def subset_expr(self, left, right):
        return Subset(left, right)

    def superset_expr(self, left, right):
        return Superset(left, right)

    def element_of_expr(self, left, right):
        return ElementOf(left, right)

    def not_element_of_expr(self, left, right):
        return NotElementOf(left, right)

    def union_expr(self, left, right):
        return Union(left, right)

    def intersect_expr(self, left, right):
        return Intersect(left, right)

    def complement_expr(self, operand):
        return Complement(operand)

    def successor_expr(self, operand):
        return Successor(operand)

    def bottom(self):
        return Bottom()

    def top(self):
        return Top()

    def emptyset(self):
        return EmptySet()

    def zero(self):
        return Zero()

    def name_expr(self, name):
        name_str = str(name)
        if name_str[0].isupper():
            return Constant(name_str)
        return Variable(name_str)

    def app_expr(self, name, args_node):
        name_str = str(name)
        args = args_node if isinstance(args_node, list) else list(args_node.children) if hasattr(args_node, 'children') else [args_node]
        if name_str[0].isupper():
            return Predicate(name_str, args)
        return FunctionApp(name_str, args)

    def args(self, *items):
        return list(items)


class FormulaParser:
    """Parse formula strings into AST nodes."""

    def __init__(self):
        self._parser = Lark(
            GRAMMAR,
            parser='earley',
            ambiguity='resolve',
        )
        self._transformer = FormulaTransformer()

    def parse(self, formula_str: str) -> ASTNode:
        """Parse a formula string into an AST.

        Args:
            formula_str: The formula string to parse.

        Returns:
            An ASTNode representing the parsed formula.

        Raises:
            ParseError: If the formula cannot be parsed.
        """
        try:
            tree = self._parser.parse(formula_str)
            result = self._transformer.transform(tree)
            return result
        except lark_exceptions.UnexpectedCharacters as e:
            raise ParseError(
                f"Unexpected character at position {e.column}: '{formula_str[e.column-1] if e.column <= len(formula_str) else '?'}'",
                line=e.line,
                column=e.column
            )
        except lark_exceptions.UnexpectedToken as e:
            raise ParseError(
                f"Unexpected token at position {e.column}: expected one of {e.expected}",
                line=e.line,
                column=e.column
            )
        except Exception as e:
            raise ParseError(f"Parse error: {str(e)}")

    def try_parse(self, formula_str: str):
        """Attempt to parse; return (ast, None) on success or (None, error_msg) on failure."""
        try:
            ast = self.parse(formula_str)
            return ast, None
        except ParseError as e:
            return None, e.message
