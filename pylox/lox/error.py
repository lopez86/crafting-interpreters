import sys

from .token import Token, TokenType


class ParseError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        super(ParseError, self).__init__(message)
        self.token = token
        self.message = message


class LoxRuntimeError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        super(LoxRuntimeError, self).__init__(message)
        self.token = token
        self.message = message


class LoxErrorHandler:
    HAD_ERROR = False
    HAD_RUNTIME_ERROR = False

    def __init__(self) -> None:
        pass

    @classmethod
    def report(cls, line: int, where: str, message: str):
        """Report something to the user."""
        sys.stderr.write(f"[Line {line}] Error{where}: {message}\n")
        LoxErrorHandler.HAD_ERROR = True

    def error(self, line: int, message: str):
        """Throw an error message."""
        self.report(line, "", message)

    def parse_error(self, error: ParseError) -> None:
        if error.token.token_type == TokenType.EOF:
            self.report(error.token.line, " at end", error.message)
        else:
            self.report(error.token.line, f" at '{error.token.lexeme}'", error.message)

    @classmethod
    def runtime_error(cls, error: LoxRuntimeError) -> None:
        sys.stderr.write(f"[Line {error.token.line}] {error.message}\n")
        LoxErrorHandler.HAD_RUNTIME_ERROR = True
