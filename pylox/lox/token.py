import enum
from typing import Optional

from .lox_object import LoxObject


class TokenType(enum.Enum):
    # Single character tokens
    LEFT_PAREN = "(",
    RIGHT_PAREN = ")",
    LEFT_BRACE = "[",
    RIGHT_BRACE = "]",
    COMMA = ",",
    DOT = ".",
    MINUS = "-",
    PLUS = "+",
    SEMICOLON = ";",
    SLASH = "/",
    STAR = "*",
    # One or two character tokens
    BANG = "!",
    BANG_EQUAL = "!=",
    EQUAL = "=",
    EQUAL_EQUAL = "==",
    GREATER = ">",
    GREATER_EQUAL = ">=",
    LESS = "<",
    LESS_EQUAL = "<=",
    # Literals
    IDENTIFIER = "~ID~"
    STRING = "~str~",
    NUMBER = "~num~",
    # Keywords
    AND = "and",
    CLASS = "class",
    ELSE = "else",
    FALSE = "false",
    FUN = "fun",
    FOR = "for",
    IF = "if",
    NIL = "nil",
    OR = "or",
    PRINT = "print",
    RETURN = "return",
    SUPER = "super",
    THIS = "this",
    TRUE = "true",
    VAR = "var",
    WHILE = "while",
    EOF = "EOF",


class Token:
    def __init__(self, token_type: TokenType, lexeme: str, literal: Optional[LoxObject], line: int) -> None:
        """A token."""
        self.token_type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self) -> str:
        """String representation of a token."""
        return f"{self.token_type} {self.lexeme} {self.literal}"
