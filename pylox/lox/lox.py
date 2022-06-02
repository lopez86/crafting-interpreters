from selectors import DefaultSelector, EVENT_READ
import signal
import socket
from typing import List

from .error import LoxErrorHandler
from .interpreter import Interpreter
from .parser import Parser
from .resolver import Resolver
from .scanner import Scanner
from .token import Token, TokenType


interrupt_read, interrupt_write = socket.socketpair()

INTERPRETER = Interpreter()


def get_interpreter() -> Interpreter:
    return INTERPRETER


def _tokens_is_empty(tokens: List[Token]) -> bool:
    if len(tokens) == 1 and tokens[0].token_type == TokenType.EOF:
        return True
    return False


def run(script: str) -> None:
    """Run some commands."""
    scanner = Scanner(script)
    tokens = scanner.scan_tokens()
    if _tokens_is_empty(tokens):
        return
    parser = Parser(tokens)
    statements = parser.parse()

    if LoxErrorHandler.HAD_ERROR:
        return
    interpreter = get_interpreter()
    resolver = Resolver(interpreter)
    resolver.resolve(statements)
    if LoxErrorHandler.HAD_ERROR:
        return
    interpreter.interpret(statements)


def run_file(file: str) -> None:
    """Run a lox script."""
    with open(file) as f:
        script = f.read()
    run(script)
    if LoxErrorHandler.HAD_ERROR is True:
        exit(65)
    if LoxErrorHandler.HAD_RUNTIME_ERROR is True:
        exit(70)


def interrupt_handler(signum, frame):
    print("Interrupting...")
    interrupt_write.send(b'\0')


signal.signal(signal.SIGINT, interrupt_handler)


def run_prompt() -> None:
    """Run with an interactive prompt."""
    sel = DefaultSelector()
    sel.register(interrupt_read, EVENT_READ)

    while True:
        try:
            line = input("> ")
        except EOFError:
            print("Quitting...")
            break

        run(line)
        LoxErrorHandler.HAD_ERROR = False
