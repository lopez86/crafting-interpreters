import abc
from typing import Generic, List, TypeVar

from .lox_object import LoxObject
from .token import Token


T = TypeVar("T")


class Expr(abc.ABC):
    def __init__(self) -> None:
        """Base type for all expressions."""
        pass

    @abc.abstractmethod
    def accept(self, visitor: "Visitor[T]") -> T:
        """Accept a visitor."""


class Assign(Expr):
    def __init__(self, name: Token, value: Expr) -> None:
        """Assign a value to a variable."""
        super(Assign, self).__init__()
        self._name = name
        self._value = value

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    @property
    def value(self) -> Expr:
        """Value."""
        return self._value

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_assign_expr(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        """Binary operation."""
        super(Binary, self).__init__()
        self._left = left
        self._operator = operator
        self._right = right

    @property
    def left(self) -> Expr:
        """Left."""
        return self._left

    @property
    def operator(self) -> Token:
        """Operator."""
        return self._operator

    @property
    def right(self) -> Expr:
        """Right."""
        return self._right

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_binary_expr(self)


class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: List[Expr]) -> None:
        """Call a function."""
        super(Call, self).__init__()
        self._callee = callee
        self._paren = paren
        self._arguments = arguments

    @property
    def callee(self) -> Expr:
        """Callee."""
        return self._callee

    @property
    def paren(self) -> Token:
        """Paren."""
        return self._paren

    @property
    def arguments(self) -> List[Expr]:
        """Arguments."""
        return self._arguments

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_call_expr(self)


class Get(Expr):
    def __init__(self, instance: Expr, name: Token) -> None:
        """Get a property of an instance."""
        super(Get, self).__init__()
        self._instance = instance
        self._name = name

    @property
    def instance(self) -> Expr:
        """Instance."""
        return self._instance

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_get_expr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr) -> None:
        """Grouping of expressions."""
        super(Grouping, self).__init__()
        self._expression = expression

    @property
    def expression(self) -> Expr:
        """Expression."""
        return self._expression

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    def __init__(self, value: LoxObject) -> None:
        """Literal value."""
        super(Literal, self).__init__()
        self._value = value

    @property
    def value(self) -> LoxObject:
        """Value."""
        return self._value

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_literal_expr(self)


class Noop(Expr):
    def __init__(self, ) -> None:
        """Null expression, does nothing."""
        super(Noop, self).__init__()

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_noop_expr(self)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        """Logical expression."""
        super(Logical, self).__init__()
        self._left = left
        self._operator = operator
        self._right = right

    @property
    def left(self) -> Expr:
        """Left."""
        return self._left

    @property
    def operator(self) -> Token:
        """Operator."""
        return self._operator

    @property
    def right(self) -> Expr:
        """Right."""
        return self._right

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_logical_expr(self)


class Set(Expr):
    def __init__(self, instance: Expr, name: Token, value: Expr) -> None:
        """Set a property on an object."""
        super(Set, self).__init__()
        self._instance = instance
        self._name = name
        self._value = value

    @property
    def instance(self) -> Expr:
        """Instance."""
        return self._instance

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    @property
    def value(self) -> Expr:
        """Value."""
        return self._value

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_set_expr(self)


class Super(Expr):
    def __init__(self, keyword: Token, method: Token) -> None:
        """Get the base class/superclass of an object."""
        super(Super, self).__init__()
        self._keyword = keyword
        self._method = method

    @property
    def keyword(self) -> Token:
        """Keyword."""
        return self._keyword

    @property
    def method(self) -> Token:
        """Method."""
        return self._method

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_super_expr(self)


class This(Expr):
    def __init__(self, keyword: Token) -> None:
        """Refer to an object inside its methods."""
        super(This, self).__init__()
        self._keyword = keyword

    @property
    def keyword(self) -> Token:
        """Keyword."""
        return self._keyword

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_this_expr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        """Unary operation."""
        super(Unary, self).__init__()
        self._operator = operator
        self._right = right

    @property
    def operator(self) -> Token:
        """Operator."""
        return self._operator

    @property
    def right(self) -> Expr:
        """Right."""
        return self._right

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_unary_expr(self)


class Variable(Expr):
    def __init__(self, name: Token) -> None:
        """Variable access"""
        super(Variable, self).__init__()
        self._name = name

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_variable_expr(self)


class Visitor(abc.ABC, Generic[T]):
    """Visitor class."""

    @abc.abstractmethod
    def visit_assign_expr(self, expr: Assign) -> T:
        """Visit class of type Assign."""

    @abc.abstractmethod
    def visit_binary_expr(self, expr: Binary) -> T:
        """Visit class of type Binary."""

    @abc.abstractmethod
    def visit_call_expr(self, expr: Call) -> T:
        """Visit class of type Call."""

    @abc.abstractmethod
    def visit_get_expr(self, expr: Get) -> T:
        """Visit class of type Get."""

    @abc.abstractmethod
    def visit_grouping_expr(self, expr: Grouping) -> T:
        """Visit class of type Grouping."""

    @abc.abstractmethod
    def visit_literal_expr(self, expr: Literal) -> T:
        """Visit class of type Literal."""

    @abc.abstractmethod
    def visit_noop_expr(self, expr: Noop) -> T:
        """Visit class of type Noop."""

    @abc.abstractmethod
    def visit_logical_expr(self, expr: Logical) -> T:
        """Visit class of type Logical."""

    @abc.abstractmethod
    def visit_set_expr(self, expr: Set) -> T:
        """Visit class of type Set."""

    @abc.abstractmethod
    def visit_super_expr(self, expr: Super) -> T:
        """Visit class of type Super."""

    @abc.abstractmethod
    def visit_this_expr(self, expr: This) -> T:
        """Visit class of type This."""

    @abc.abstractmethod
    def visit_unary_expr(self, expr: Unary) -> T:
        """Visit class of type Unary."""

    @abc.abstractmethod
    def visit_variable_expr(self, expr: Variable) -> T:
        """Visit class of type Variable."""
