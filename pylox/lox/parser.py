from typing import List, Optional

from .error import LoxErrorHandler, ParseError
from .expression import (
    Assign,
    Binary,
    Call,
    Expr,
    Get,
    Grouping,
    Literal,
    Logical,
    Set,
    Super,
    This,
    Unary,
    Variable,
)
from .lox_types import LOX_TRUE, LOX_FALSE, LOX_NIL
from .statement import Block, Class, Expression, Function, If, Null, Print, Return, Stmt, Var, While
from .token import Token, TokenType


error_handler = LoxErrorHandler()

ARGS_MAX_SIZE = 255


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        """The parser takes tokens and produces a list of statements.

        It has to manage a bunch of state, so the parser takes tokens at initialization.

        Args:
            tokens: list of Token, the tokens to process into statements.
        """
        self._tokens = tokens
        self._current = 0

    def parse(self) -> List[Stmt]:
        """Parse the tokens."""
        statements = []
        while not self.is_at_end():
            statements.append(self._declaration())
        return statements

    def _declaration(self) -> Optional[Stmt]:
        """Match to declaration statements.

        This handles class, function, and variable declarations. If these don't match,
        go to all other statement types.

        Returns:
            maybe Stmt, will be None if an error occurs.
        """
        try:
            if self._match(TokenType.CLASS):
                return self._class_declaration()
            if self._match(TokenType.FUN):
                return self._function("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _class_declaration(self) -> Class:
        """Create a class declaration statement.

        A class is in the form

        class Bagel < Breakfast {
            init(toppings) {
                this.toppings = toppings;
            }

            eat() {
                print "Eating a bagel.";
            }
        }

        Returns:
            Class
        """
        name = self._consume(TokenType.IDENTIFIER, "Expect class name.")
        if self._match(TokenType.LESS):
            self._consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = Variable(self._previous())
        else:
            superclass = None

        self._consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")
        methods = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self._function("method"))
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return Class(name, superclass, methods)

    def _function(self, kind: str) -> Function:
        """Declare a function."""
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []
        if not self._check(TokenType.RIGHT_PAREN):
            parameters.append(self._consume(TokenType.IDENTIFIER, "Expect parameter name."))
            while self._match(TokenType.COMMA):
                parameters.append(self._consume(TokenType.IDENTIFIER, "Expect parameter name."))
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self._consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return Function(name, parameters, body)

    def _var_declaration(self) -> Stmt:
        """Declare a variable."""
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        else:
            initializer = Literal(LOX_NIL)
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def _statement(self) -> Stmt:
        """Process other statement types, else move to expressions."""
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LEFT_BRACE):
            return Block(self._block())
        return self._expression_statement()

    def _block(self) -> List[Stmt]:
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self._declaration())
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value = LOX_NIL
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)

    def _print_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def _expression_statement(self) -> Stmt:
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def _if_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self._statement()
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        else:
            else_branch = Null()
        return If(condition, then_branch, else_branch)

    def _for_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")
        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")
        body = self._statement()
        if increment is not None:
            body = Block(
                [body, Expression(increment)]
            )
        if condition is None:
            condition = Literal(LOX_TRUE)
        body = While(condition, body)
        if initializer is not None:
            body = Block([initializer, body])
        return body

    def _while_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body = self._statement()
        return While(condition, body)

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._or()
        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)
            elif isinstance(expr, Get):
                return Set(expr.instance, expr.name, value)

            else:
                self._error(equals, "Invalid assignment target.")

        return expr

    def _or(self) -> Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = Logical(expr, operator, right)
        return expr

    def _and(self) -> Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = Logical(expr, operator, right)
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()

        while self._multimatch([TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL]):
            operator = self._previous()
            right = self._comparison()
            expr = Binary(expr, operator, right)

        return expr

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._multimatch(
            [TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL]
        ):
            operator = self._previous()
            right = self._term()
            expr = Binary(expr, operator, right)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._multimatch([TokenType.PLUS, TokenType.MINUS]):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._multimatch([TokenType.SLASH, TokenType.STAR]):
            operator = self._previous()
            right = self._unary()
            expr = Binary(expr, operator, right)
        return expr

    def _unary(self) -> Expr:
        if self._multimatch([TokenType.BANG, TokenType.MINUS]):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)
        return self._call()

    def _call(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.DOT):
                name = self._consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            else:
                break
        return expr

    def _finish_call(self, callee: Expr) -> Expr:
        args = []
        if not self._check(TokenType.RIGHT_PAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                if len(args) >= ARGS_MAX_SIZE:
                    self._error(self._peek(), f"Can't have more than {ARGS_MAX_SIZE} arguments.")
                args.append(self._expression())

        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee, paren, args)

    def _primary(self) -> Expr:
        if self._match(TokenType.FALSE):
            return Literal(LOX_FALSE)
        if self._match(TokenType.TRUE):
            return Literal(LOX_TRUE)
        if self._match(TokenType.NIL):
            return Literal(LOX_NIL)
        if self._multimatch([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self._previous().literal)
        if self._match(TokenType.THIS):
            return This(self._previous())
        if self._match(TokenType.SUPER):
            keyword = self._previous()
            self._consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self._consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return Super(keyword, method)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        self._error(self._peek(), "Could not match token.")

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self._peek().token_type == token_type

    def _multimatch(self, token_types: List[TokenType]) -> bool:
        if self._multicheck(token_types):
            self._advance()
            return True
        return False

    def _multicheck(self, token_types: List[TokenType]) -> bool:
        if self.is_at_end():
            return False
        return self._peek().token_type in token_types

    def _advance(self) -> Token:
        if not self.is_at_end():
            self._current += 1
        return self._previous()

    def is_at_end(self) -> bool:
        return self._peek().token_type == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self):
        return self._tokens[self._current - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()

        raise self._error(self._peek(), message)

    @classmethod
    def _error(cls, token: Token, message: str) -> ParseError:
        error = ParseError(token, message)
        error_handler.parse_error(error)
        return error

    def _synchronize(self) -> None:
        """Try to move to beginning of next statement."""
        self._advance()
        while not self.is_at_end():
            if self._previous().token_type == TokenType.SEMICOLON:
                return
            if self._peek().token_type in [
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ]:
                return
            self._advance()
