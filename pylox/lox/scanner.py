"""The scanner simply scans the text of the input to produce tokens of various kinds.

Basically, it searches for keywords, special character operators, and anything else is taken
to be a variable name.

This implementation only looks up to one character ahead and has no super complicated logic,
which is actually fine - anything complicated might be bad for users anyway.
"""

from typing import List, Optional

from .error import LoxErrorHandler
from .lox_types import LoxNumber, LoxString
from .lox_object import LoxObject
from .token import Token, TokenType


error_handler = LoxErrorHandler()


# Reserved keywords
KEYWORD_TO_TOKEN_TYPE = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "fun": TokenType.FUN,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
}


def is_alpha(c: str) -> bool:
    """Check if a character is alphabetic or underscore."""
    return c.isalpha() or c == "_"


class Scanner:
    def __init__(self, source: str) -> None:
        """Scans source for tokens.

        Args:
            source: str, the source code to scan.
        """
        self._source = source
        self._tokens = []
        self._current = 0
        self._start = 0
        self._line = 1

    def is_at_end(self) -> bool:
        """Are we at the end of the source?"""
        return self._current >= len(self._source)

    def scan_tokens(self) -> List[Token]:
        """Scan for tokens."""
        while not self.is_at_end():
            self._start = self._current
            self.scan_token()
        self._tokens.append(Token(TokenType.EOF, "", None, self._line))
        return self._tokens

    def scan_token(self) -> None:
        """Scan for the next token.

        Many of the special characters are only used at the beginning of a single operator
        so they are very easy to find - just search for that character at the beginning of a
        token.

        For others, you need more complicated logic to choose between operators (like > and
        >= -- need to look ahead to the next character to see if it matches.
        """
        c = self.advance()
        # Handle single character
        if c == "(":
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ")":
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == "{":
            self.add_token(TokenType.LEFT_BRACE)
        elif c == "}":
            self.add_token(TokenType.RIGHT_BRACE)
        elif c == ",":
            self.add_token(TokenType.COMMA)
        elif c == ".":
            self.add_token(TokenType.DOT)
        elif c == "-":
            self.add_token(TokenType.MINUS)
        elif c == "+":
            self.add_token(TokenType.PLUS)
        elif c == ";":
            self.add_token(TokenType.SEMICOLON)
        elif c == "*":
            self.add_token(TokenType.STAR)
        elif c == "!":
            token_type = TokenType.BANG_EQUAL if self.match_advance("=") else TokenType.BANG
            self.add_token(token_type)
        elif c == "=":
            token_type = TokenType.EQUAL_EQUAL if self.match_advance("=") else TokenType.EQUAL
            self.add_token(token_type)
        elif c == "<":
            token_type = TokenType.LESS_EQUAL if self.match_advance("=") else TokenType.LESS
            self.add_token(token_type)
        elif c == ">":
            token_type = TokenType.GREATER_EQUAL if self.match_advance("=") else TokenType.GREATER
            self.add_token(token_type)
        elif c == "/":
            # Handle comment
            if self.match_advance("/"):
                while self.peek() != "\n" and self.is_at_end() is False:
                    self.advance()

            else:
                self.add_token(TokenType.SLASH)
        elif c in " \r\t":
            pass
        elif c == "\n":
            self._line += 1
        elif c == "\"":
            self.add_string()
        elif c.isdigit():
            self.add_number()
        elif is_alpha(c):
            self.add_identifier()
        else:
            error_handler.error(self._line, "Unexpected character.")

    def match_advance(self, expected: str) -> bool:
        """Advance to the next character only if it matches the expected one.

        Args:
            expected: str, the next character we expect if we want to advance.
        """
        if self.is_at_end():
            return False
        if self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def advance(self) -> str:
        """Advance one character."""
        c = self._source[self._current]
        self._current += 1
        return c

    def peek(self) -> str:
        """Look at the current character."""
        if self.is_at_end():
            return "\0"
        return self._source[self._current]

    def peek_next(self) -> str:
        """Look at the next character."""
        if self._current + 1 >= len(self._source):
            return "\0"
        return self._source[self._current + 1]

    def add_token(self, token_type: TokenType, literal: Optional[LoxObject] = None) -> None:
        """Add a token."""
        text = self._source[self._start: self._current]
        self._tokens.append(Token(token_type, text, literal, self._line))

    def add_string(self) -> None:
        """Add a string. Keeps adding characters until it finds the next quotation mark.

        Escaping not allowed right now, so double quotes are reserved only for string
        starting & termination.
        """
        while self.peek() != "\"" and not self.is_at_end():
            if self.peek() == "\n":
                self._line += 1
            self.advance()
        if self.is_at_end():
            error_handler.error(self._line, "Unterminated string.")
            return
        self.advance()
        value = LoxString(self._source[self._start + 1: self._current - 1])
        self.add_token(TokenType.STRING, value)

    def add_number(self) -> None:
        """Add a floating-point number."""
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()

        value = LoxNumber(float(self._source[self._start: self._current]))
        self.add_token(TokenType.NUMBER, value)

    def add_identifier(self) -> None:
        """Add an identifier. Identifiers can only contain alphabetic or underscore."""
        while is_alpha(self.peek()):
            self.advance()
        text = self._source[self._start: self._current]
        token_type = KEYWORD_TO_TOKEN_TYPE.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)
