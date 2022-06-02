import abc
from typing import Generic, List, Optional, TypeVar

from .expression import Expr, Variable
from .token import Token


T = TypeVar("T")


class Stmt(abc.ABC):
    def __init__(self) -> None:
        """Base type for all statements."""
        pass

    @abc.abstractmethod
    def accept(self, visitor: "Visitor[T]") -> T:
        """Accept a visitor."""


class Block(Stmt):
    def __init__(self, statements: List[Stmt]) -> None:
        """Block of statements."""
        super(Block, self).__init__()
        self._statements = statements

    @property
    def statements(self) -> List[Stmt]:
        """Statements."""
        return self._statements

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_block_stmt(self)


class Class(Stmt):
    def __init__(self, name: Token, superclass: Optional[Variable], methods: List["Function"]) -> None:
        """Class definition."""
        super(Class, self).__init__()
        self._name = name
        self._superclass = superclass
        self._methods = methods

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    @property
    def superclass(self) -> Optional[Variable]:
        """Superclass."""
        return self._superclass

    @property
    def methods(self) -> List["Function"]:
        """Methods."""
        return self._methods

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_class_stmt(self)


class Expression(Stmt):
    def __init__(self, expression: Expr) -> None:
        """Expression statement."""
        super(Expression, self).__init__()
        self._expression = expression

    @property
    def expression(self) -> Expr:
        """Expression."""
        return self._expression

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    def __init__(self, name: Token, params: List[Token], body: List[Stmt]) -> None:
        """Function definition."""
        super(Function, self).__init__()
        self._name = name
        self._params = params
        self._body = body

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    @property
    def params(self) -> List[Token]:
        """Params."""
        return self._params

    @property
    def body(self) -> List[Stmt]:
        """Body."""
        return self._body

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_function_stmt(self)


class If(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt) -> None:
        """If/else block."""
        super(If, self).__init__()
        self._condition = condition
        self._then_branch = then_branch
        self._else_branch = else_branch

    @property
    def condition(self) -> Expr:
        """Condition."""
        return self._condition

    @property
    def then_branch(self) -> Stmt:
        """Then_branch."""
        return self._then_branch

    @property
    def else_branch(self) -> Stmt:
        """Else_branch."""
        return self._else_branch

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_if_stmt(self)


class Null(Stmt):
    def __init__(self, ) -> None:
        """Null statement. Do nothing."""
        super(Null, self).__init__()

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_null_stmt(self)


class Print(Stmt):
    def __init__(self, expression: Expr) -> None:
        """Print statement."""
        super(Print, self).__init__()
        self._expression = expression

    @property
    def expression(self) -> Expr:
        """Expression."""
        return self._expression

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: Token, value: Optional[Expr]) -> None:
        """Return statement."""
        super(Return, self).__init__()
        self._keyword = keyword
        self._value = value

    @property
    def keyword(self) -> Token:
        """Keyword."""
        return self._keyword

    @property
    def value(self) -> Optional[Expr]:
        """Value."""
        return self._value

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_return_stmt(self)


class Var(Stmt):
    def __init__(self, name: Token, initializer: Expr) -> None:
        """Variable statement"""
        super(Var, self).__init__()
        self._name = name
        self._initializer = initializer

    @property
    def name(self) -> Token:
        """Name."""
        return self._name

    @property
    def initializer(self) -> Expr:
        """Initializer."""
        return self._initializer

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_var_stmt(self)


class While(Stmt):
    def __init__(self, condition: Expr, body: Stmt) -> None:
        """While loop."""
        super(While, self).__init__()
        self._condition = condition
        self._body = body

    @property
    def condition(self) -> Expr:
        """Condition."""
        return self._condition

    @property
    def body(self) -> Stmt:
        """Body."""
        return self._body

    def accept(self, visitor: "Visitor[T]") -> T:
        """Call a visitor."""
        return visitor.visit_while_stmt(self)


class Visitor(abc.ABC, Generic[T]):
    """Visitor class."""

    @abc.abstractmethod
    def visit_block_stmt(self, stmt: Block) -> T:
        """Visit class of type Block."""

    @abc.abstractmethod
    def visit_class_stmt(self, stmt: Class) -> T:
        """Visit class of type Class."""

    @abc.abstractmethod
    def visit_expression_stmt(self, stmt: Expression) -> T:
        """Visit class of type Expression."""

    @abc.abstractmethod
    def visit_function_stmt(self, stmt: Function) -> T:
        """Visit class of type Function."""

    @abc.abstractmethod
    def visit_if_stmt(self, stmt: If) -> T:
        """Visit class of type If."""

    @abc.abstractmethod
    def visit_null_stmt(self, stmt: Null) -> T:
        """Visit class of type Null."""

    @abc.abstractmethod
    def visit_print_stmt(self, stmt: Print) -> T:
        """Visit class of type Print."""

    @abc.abstractmethod
    def visit_return_stmt(self, stmt: Return) -> T:
        """Visit class of type Return."""

    @abc.abstractmethod
    def visit_var_stmt(self, stmt: Var) -> T:
        """Visit class of type Var."""

    @abc.abstractmethod
    def visit_while_stmt(self, stmt: While) -> T:
        """Visit class of type While."""
