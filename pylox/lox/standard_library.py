import time
from typing import TYPE_CHECKING, List

from .environment import Environment
from .lox_types import LoxCallable, LoxNumber
from .lox_object import LoxObject

if TYPE_CHECKING:
    from .interpreter import Interpreter


class Clock(LoxCallable):
    name = "clock"
    arity = 0

    def __init__(self):
        super(Clock, self).__init__(self.name, self.arity)

    def call(self, interpreter: "Interpreter", args: List[LoxObject]) -> LoxObject:
        return LoxNumber(time.time())

    def __str__(self) -> str:
        return "<native fn>"


def make_standard_environment() -> Environment:
    env = Environment()
    env.define(Clock.name, Clock())
    return env
