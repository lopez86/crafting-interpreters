from contextlib import contextmanager
import enum
from typing import Dict, List, Sequence

from .error import LoxErrorHandler
from .expression import (
    Assign,
    Binary,
    Call,
    Expr,
    Get,
    Grouping,
    Literal,
    Logical,
    Noop,
    Set,
    Super,
    This,
    Unary,
    Variable,
    Visitor as ExprVisitor,
)
from .interpreter import Interpreter
from .lox_types import LoxNil
from .statement import (
    Block,
    Class,
    Expression,
    If,
    Function,
    Null,
    Print,
    Return,
    Stmt,
    Var,
    Visitor as StmtVisitor,
    While,
)
from .token import Token


error_handler = LoxErrorHandler()


class FunctionType(enum.Enum):
    Function = 0
    Initializer = 1
    Method = 2
    NoFunction = 3


class ClassType(enum.Enum):
    NONE = 0
    CLASS = 1
    SUBCLASS = 2


class Resolver(ExprVisitor[None], StmtVisitor[None]):
    def __init__(self, interpreter: Interpreter) -> None:
        super(Resolver, self).__init__()
        self._interpreter = interpreter
        self._scopes: List[Dict[str, bool]] = []
        self._current_function = FunctionType.NoFunction
        self._current_class = ClassType.NONE

    @contextmanager
    def set_function_type(self, function_type: FunctionType) -> None:
        """Context manager to set the function type and revert when done."""
        existing_function_type = self._current_function
        self._current_function = function_type
        try:
            yield
        finally:
            self._current_function = existing_function_type

    @contextmanager
    def set_class_type(self, class_type: ClassType) -> None:
        """Context manager to set the class type and revert when done."""
        existing_class = self._current_class
        self._current_class = class_type
        try:
            yield
        finally:
            self._current_class = existing_class

    @contextmanager
    def new_scope(self, create: bool) -> None:
        """Context manager to create and end a scope."""
        if create:
            self._begin_scope()
        try:
            yield
        finally:
            if create:
                self._end_scope()

    def visit_block_stmt(self, stmt: Block) -> None:
        with self.new_scope(True):
            self.resolve(stmt.statements)

    def visit_var_stmt(self, stmt: Var) -> None:
        self._declare(stmt.name)
        if not isinstance(stmt.initializer, Literal) or isinstance(stmt.initializer, LoxNil):
            self._resolve_expression(stmt.initializer)
        self._define(stmt.name)

    def visit_function_stmt(self, stmt: Function) -> None:
        self._declare(stmt.name)
        self._define(stmt.name)
        self._resolve_function(stmt, FunctionType.Function)

    def visit_expression_stmt(self, stmt: Expression) -> None:
        self._resolve_expression(stmt.expression)

    def visit_variable_expr(self, expr: Variable) -> None:
        if self._scopes and self._scopes[-1][expr.name.lexeme] is False:
            error_handler.error(expr.name.line, "Can't read local variable in its own initializer.")
        self._resolve_local(expr, expr.name)

    def visit_if_stmt(self, stmt: If) -> None:
        self._resolve_expression(stmt.condition)
        self._resolve_statement(stmt.then_branch)
        self._resolve_statement(stmt.else_branch)

    def visit_print_stmt(self, stmt: Print) -> None:
        self._resolve_expression(stmt.expression)

    def visit_return_stmt(self, stmt: Return) -> None:
        if self._current_function == FunctionType.NoFunction:
            error_handler.error(stmt.keyword.line, "Can't return from top-level code.")
        if stmt.value is not None:
            if self._current_function == FunctionType.Initializer:
                error_handler.error(stmt.keyword.line, "Can't return a value from an initializer.")
            self._resolve_expression(stmt.value)

    def visit_while_stmt(self, stmt: While) -> None:
        self._resolve_expression(stmt.condition)
        self._resolve_statement(stmt.body)

    def visit_class_stmt(self, stmt: Class):
        with self.set_class_type(ClassType.CLASS):
            self._declare(stmt.name)
            self._define(stmt.name)
            has_superclass = stmt.superclass is not None
            if has_superclass:
                if stmt.name.lexeme == stmt.superclass.name.lexeme:
                    error_handler.error(stmt.name.line, "A class can't inherit from itself.")
                self._current_class = ClassType.SUBCLASS
                self._resolve_expression(stmt.superclass)

            with self.new_scope(has_superclass):

                if has_superclass:
                    self._scopes[-1]["super"] = True
                with self.new_scope(True):
                    self._scopes[-1]["this"] = True
                    for method in stmt.methods:
                        if method.name.lexeme == "init":
                            declaration = FunctionType.Initializer
                        else:
                            declaration = FunctionType.Method
                        self._resolve_function(method, declaration)

    def visit_null_stmt(self, stmt: Null) -> None:
        return

    def visit_assign_expr(self, expr: Assign) -> None:
        self._resolve_expression(expr.value)
        self._resolve_local(expr, expr.name)

    def visit_binary_expr(self, expr: Binary) -> None:
        self._resolve_expression(expr.left)
        self._resolve_expression(expr.right)

    def visit_call_expr(self, expr: Call) -> None:
        self._resolve_expression(expr.callee)
        for arg in expr.arguments:
            self._resolve_expression(arg)

    def visit_grouping_expr(self, expr: Grouping) -> None:
        self._resolve_expression(expr.expression)

    def visit_literal_expr(self, expr: Literal) -> None:
        return

    def visit_logical_expr(self, expr: Logical) -> None:
        self._resolve_expression(expr.left)
        self._resolve_expression(expr.right)

    def visit_noop_expr(self, expr: Noop) -> None:
        return

    def visit_unary_expr(self, expr: Unary) -> None:
        self._resolve_expression(expr.right)

    def visit_get_expr(self, expr: Get) -> None:
        self._resolve_expression(expr.instance)

    def visit_set_expr(self, expr: Set) -> None:
        self._resolve_expression(expr.value)
        self._resolve_expression(expr.instance)

    def visit_this_expr(self, expr: This) -> None:
        if self._current_class == ClassType.NONE:
            error_handler.error(expr.keyword.line, "Can't use 'this' outside of a class.")
            return
        self._resolve_local(expr, expr.keyword)

    def visit_super_expr(self, expr: Super) -> None:
        if self._current_class == ClassType.NONE:
            error_handler.error(expr.keyword.line, "Can't use 'super' outside of a class.")
        if self._current_class != ClassType.SUBCLASS:
            error_handler.error(
                expr.keyword.line, "Can't use 'super' in a class with no subclass."
            )
        self._resolve_local(expr, expr.keyword)

    def _resolve_local(self, expr: Expr, name: Token) -> None:
        for idx, scope in enumerate(reversed(self._scopes)):
            if name.lexeme in scope:
                self._interpreter.resolve(expr, idx)

    def _begin_scope(self) -> None:
        self._scopes.append({})

    def _end_scope(self) -> None:
        self._scopes.pop()

    def _declare(self, name: Token) -> None:
        if not self._scopes:
            return
        scope = self._scopes[-1]
        if name.lexeme in scope:
            error_handler.error(
                name.line, f"Already a variable with the name '{name.lexeme}' in this scope."
            )
        scope[name.lexeme] = False

    def _define(self, name: Token) -> None:
        if not self._scopes:
            return
        scope = self._scopes[-1]
        scope[name.lexeme] = True

    def resolve(self, statements: Sequence[Stmt]) -> None:
        for statement in statements:
            self._resolve_statement(statement)

    def _resolve_statement(self, statement: Stmt) -> None:
        statement.accept(self)

    def _resolve_expression(self, expression: Expr) -> None:
        expression.accept(self)

    def _resolve_function(self, function: Function, function_type: FunctionType) -> None:
        with self.set_function_type(function_type):
            with self.new_scope(True):
                for param in function.params:
                    self._declare(param)
                    self._define(param)
                self.resolve(function.body)
