from contextlib import contextmanager
import copy
from typing import Dict, Sequence, Tuple

from .environment import Environment
from .error import LoxErrorHandler, LoxRuntimeError
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
from .lox_types import (
    LOX_NIL,
    LoxBool,
    LoxCallable,
    LoxClass,
    LoxFunction,
    LoxInstance,
    LoxNil,
    LoxNumber,
    LoxString,
    ReturnState,
)
from .lox_object import LoxObject
from .standard_library import make_standard_environment
from .statement import (
    Block,
    Class,
    Expression,
    Function,
    If,
    Null,
    Print,
    Return,
    Stmt,
    Var,
    Visitor as StmtVisitor,
    While,
)
from .token import Token, TokenType


error_handler = LoxErrorHandler()


def stringify(lox_object: LoxObject) -> str:
    if isinstance(lox_object, LoxNil):
        return "nil"
    if isinstance(lox_object, LoxNumber):
        text = str(lox_object.value)
        if text.endswith(".0"):
            text = text[:-2]
        return text
    return str(lox_object)


def is_truthy(lox_object: LoxObject) -> bool:
    if isinstance(lox_object, LoxNil):
        return False
    if isinstance(lox_object, LoxBool):
        return lox_object.value
    return True


def check_is_numeric(token: Token, lox_object: LoxObject) -> LoxNumber:
    if not isinstance(lox_object, LoxNumber):
        raise LoxRuntimeError(token, "Operator must be a number.")
    return lox_object


def check_numeric_operands(
    token: Token, left: LoxObject, right: LoxObject
) -> Tuple[LoxNumber, LoxNumber]:
    return check_is_numeric(token, left), check_is_numeric(token, right)


def is_equal(left: LoxObject, right: LoxObject) -> bool:
    if isinstance(left, LoxNil) and isinstance(right, LoxNil):
        return True
    if isinstance(left, LoxNil):
        return False
    return left.equals(right)


class Interpreter(ExprVisitor[LoxObject], StmtVisitor[None]):
    def __init__(self) -> None:
        super(Interpreter, self).__init__()
        self._globals = make_standard_environment()
        self._environment = copy.copy(self._globals)
        self._locals: Dict[Expr, int] = {}

    @contextmanager
    def new_environment(self, use_new: bool = True) -> None:
        if use_new:
            self._environment = Environment(self._environment)
        try:
            yield
        finally:
            if use_new:
                self._environment = self._environment.enclosing

    @property
    def globals(self) -> Environment:
        return self._globals

    def resolve(self, expr: Expr, depth: int) -> None:
        self._locals[expr] = depth

    def interpret(self, statements: Sequence[Stmt]):
        try:
            for statement in statements:
                self._execute(statement)
        except LoxRuntimeError as err:
            error_handler.runtime_error(err)

    def visit_block_stmt(self, stmt: Block) -> None:
        self.execute_block(stmt.statements, Environment(self._environment))

    def execute_block(self, statements: Sequence[Stmt], environment: Environment) -> None:
        previous = self._environment
        try:
            self._environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self._environment = previous

    def visit_print_stmt(self, stmt: Print) -> None:
        value = self._evaluate(stmt.expression)
        print(stringify(value))

    def visit_expression_stmt(self, stmt: Expression) -> None:
        self._evaluate(stmt.expression)

    def visit_function_stmt(self, stmt: Function) -> None:
        function = LoxFunction(stmt, self._environment, False)
        self._environment.define(stmt.name.lexeme, function)

    def visit_var_stmt(self, stmt: Var) -> None:
        initializer = stmt.initializer
        if (
            isinstance(initializer, Literal) and
            isinstance(initializer.value, LoxNil)
        ):
            value = LOX_NIL
        else:
            value = self._evaluate(stmt.initializer)
        self._environment.define(stmt.name.lexeme, value)

    def visit_if_stmt(self, stmt: If) -> None:
        if is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        else:
            self._execute(stmt.else_branch)

    def visit_while_stmt(self, stmt: While) -> None:
        while is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def visit_class_stmt(self, stmt: Class) -> None:
        if stmt.superclass is not None:
            superclass = self._evaluate(stmt.superclass)
            if not isinstance(superclass, LoxClass):
                raise LoxRuntimeError(stmt.superclass.name, "Superclass must be a class.")

        else:
            superclass = None
        self._environment.define(stmt.name.lexeme, LOX_NIL)

        with self.new_environment(superclass is not None):
            self._environment.define("super", superclass)

            methods: Dict[str, LoxFunction] = {}
            for method in stmt.methods:
                if method.name.lexeme == "init":
                    is_init = True
                else:
                    is_init = False
                function = LoxFunction(method, self._environment, is_init)
                methods[method.name.lexeme] = function

            klass = LoxClass(stmt.name.lexeme, superclass, methods)

        self._environment.assign(stmt.name, klass)

    def visit_null_stmt(self, stmt: Null) -> None:
        return

    def visit_return_stmt(self, stmt: Return) -> None:
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        else:
            value = LOX_NIL
        raise ReturnState(value)

    def visit_noop_expr(self, expr: Noop) -> LoxObject:
        return LOX_NIL

    def visit_call_expr(self, expr: Call) -> LoxObject:
        function = self._evaluate(expr.callee)
        if not isinstance(function, LoxCallable):
            raise LoxRuntimeError(expr.paren, "Can only call functions and classes.")
        args = []
        for arg in expr.arguments:
            args.append(self._evaluate(arg))
        if len(args) != function.arity:
            raise LoxRuntimeError(
                expr.paren, f"Expected {function.arity} args but got {len(args)}."
            )
        return function.call(self, args)

    def visit_get_expr(self, expr: Get) -> LoxObject:
        instance = self._evaluate(expr.instance)
        if isinstance(instance, LoxInstance):
            return instance.get(expr.name)
        raise LoxRuntimeError(expr.name, "Only instances have properties.")

    def visit_set_expr(self, expr: Set) -> LoxObject:
        instance = self._evaluate(expr.instance)
        if not isinstance(instance, LoxInstance):
            raise LoxRuntimeError(expr.name, "Only instances have fields.")
        value = self._evaluate(expr.value)
        instance.set(expr.name, value)
        return value

    def visit_literal_expr(self, expr: Literal) -> LoxObject:
        return expr.value

    def visit_logical_expr(self, expr: Logical) -> LoxObject:
        left = self._evaluate(expr.left)
        if expr.operator.token_type == TokenType.OR:
            if is_truthy(left):
                return left
        else:
            if not is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def visit_grouping_expr(self, expr: Grouping) -> LoxObject:
        return self._evaluate(expr.expression)

    def visit_unary_expr(self, expr: Unary) -> LoxObject:
        right = self._evaluate(expr.right)
        if expr.operator.token_type == TokenType.MINUS:
            right_num = check_is_numeric(expr.operator, right)
            return LoxNumber(-right_num.value)
        elif expr.operator.token_type == TokenType.BANG:
            return LoxBool(not is_truthy(right))
        else:
            pass
        return LOX_NIL

    def visit_binary_expr(self, expr: Binary) -> LoxObject:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op_type = expr.operator.token_type
        if op_type == TokenType.PLUS:
            if isinstance(left, LoxNumber) and isinstance(right, LoxNumber):
                return LoxNumber(left.value + right.value)
            elif isinstance(left, LoxString) and isinstance(right, LoxString):
                return LoxString(left.value + right.value)
            else:
                raise LoxRuntimeError(expr.operator, "Args must be either Number or String.")
        elif op_type == TokenType.MINUS:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxNumber(left_num.value - right_num.value)
        elif op_type == TokenType.SLASH:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxNumber(left_num.value / right_num.value)
        elif op_type == TokenType.STAR:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxNumber(left_num.value * right_num.value)
        elif op_type == TokenType.GREATER:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxBool(left_num.value > right_num.value)
        elif op_type == TokenType.GREATER_EQUAL:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxBool(left_num.value >= right_num.value)
        elif op_type == TokenType.LESS:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxBool(left_num.value < right_num.value)
        elif op_type == TokenType.LESS_EQUAL:
            left_num, right_num = check_numeric_operands(expr.operator, left, right)
            return LoxBool(left_num.value <= right_num.value)
        elif op_type == TokenType.BANG_EQUAL:
            return LoxBool(not is_equal(left, right))
        elif op_type == TokenType.EQUAL_EQUAL:
            return LoxBool(is_equal(left, right))
        else:
            pass
        return LOX_NIL

    def visit_variable_expr(self, expr: Variable) -> LoxObject:
        return self._environment.get(expr.name)

    def visit_assign_expr(self, expr: Assign) -> LoxObject:
        value = self._evaluate(expr.value)
        self._environment.assign(expr.name, value)
        return value

    def visit_this_expr(self, expr: This) -> LoxObject:
        return self._look_up_variable(expr.keyword, expr)

    def visit_super_expr(self, expr: Super) -> LoxObject:
        distance = self._locals.get(expr)
        if distance is None:
            raise AssertionError("Coding error. Should not be here.")
        superclass = self._environment.get_at(distance, "super")
        if not isinstance(superclass, LoxClass):
            raise AssertionError("Coding error. 'super' must refer to a class.")
        instance = self._environment.get_at(distance - 1, "this")
        if not isinstance(instance, LoxInstance):
            raise AssertionError("Coding error. 'this' must refer to an instance.")
        method = superclass.find_method(expr.method.lexeme)
        if method is None:
            raise LoxRuntimeError(expr.method, f"Undefined property {expr.method.lexeme}.")
        return method.bind(instance)

    def _evaluate(self, expr: Expr) -> LoxObject:
        return expr.accept(self)

    def _execute(self, stmt: Stmt) -> None:
        return stmt.accept(self)

    def _look_up_variable(self, name: Token, expr: Expr) -> LoxObject:
        distance = self._locals.get(expr)
        if distance is not None:
            return self._environment.get_at(distance, name.lexeme)
        return self._globals.get(name)
