from typing import Dict, Optional

from .error import LoxRuntimeError
from .lox_object import LoxObject
from .token import Token


class Environment:
    def __init__(self, enclosing: Optional["Environment"] = None) -> None:
        """The environment holds """
        self._values: Dict[str, LoxObject] = {}
        self._enclosing = enclosing

    @property
    def enclosing(self) -> "Environment":
        return self._enclosing

    def define(self, name: str, value: LoxObject) -> None:
        self._values[name] = value

    def get(self, name: Token) -> LoxObject:
        value = self._values.get(name.lexeme)
        if value is not None:
            return value
        if self._enclosing is not None:
            return self._enclosing.get(name)

        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: LoxObject) -> None:
        if name.lexeme in self._values:
            self._values[name.lexeme] = value
            return
        if self._enclosing is not None:
            self._enclosing.assign(name, value)
            return
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def get_at(self, distance: int, name: str) -> LoxObject:
        return self._ancestor(distance)._values[name]

    def _ancestor(self, distance: int) -> "Environment":
        env = self
        for _ in range(distance):
            env = env._enclosing
        return env

    def assign_at(self, distance: int, name: Token, value: LoxObject) -> None:
        self._ancestor(distance)._values[name.lexeme] = value

