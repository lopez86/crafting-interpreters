from typing import List

from .expression import (
    Binary,
    Expr,
    Grouping,
    Literal,
    Unary,
    Visitor,
)


class AstPrinter(Visitor[str]):
    def _parenthesize(self, name: str, data: List[Expr]) -> str:
        if data:
            return f"({name} {' '.join(expr.accept(self) for expr in data)})"

    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_binary_expr(self, expr: Binary) -> str:
        return self._parenthesize(expr.operator.lexeme, [expr.left, expr.right])

    def visit_unary_expr(self, expr: Unary) -> str:
        return self._parenthesize(expr.operator.lexeme, [expr.right])

    def visit_grouping_expr(self, expr: Grouping) -> str:
        return self._parenthesize("group", [expr.expression])

    def visit_literal_expr(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)
