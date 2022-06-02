import abc
from typing import TYPE_CHECKING, Dict, List, Optional

from .lox_object import LoxObject
from .environment import Environment
from .statement import Function
from .token import Token

if TYPE_CHECKING:
    from .interpreter import Interpreter


class LoxString(LoxObject):
    def __init__(self, value: str) -> None:
        super(LoxString, self).__init__()
        self._value = value

    def __str__(self) -> str:
        return self._value

    def equals(self, other: LoxObject) -> bool:
        if isinstance(other, LoxString) and other.value == self._value:
            return True
        return False

    @property
    def value(self) -> str:
        return self._value


class LoxNumber(LoxObject):
    def __init__(self, value: float) -> None:
        super(LoxNumber, self).__init__()
        self._value = value

    def equals(self, other: LoxObject) -> bool:
        if isinstance(other, LoxNumber) and other.value == self._value:
            return True
        return False

    def __str__(self) -> str:
        return f"LoxString<{self._value}>"

    @property
    def value(self) -> float:
        return self._value


class LoxBool(LoxObject):
    def __init__(self, value: bool) -> None:
        super(LoxBool, self).__init__()
        self._value = value

    def equals(self, other: LoxObject) -> bool:
        if isinstance(other, LoxBool) and other.value == self._value:
            return True
        return False

    @property
    def value(self) -> bool:
        return self._value

    def __str__(self) -> str:
        return f"{self._value}"


class LoxCallable(LoxObject, abc.ABC):
    def __init__(self, function_name: str, arity: int) -> None:
        super(LoxCallable, self).__init__()
        self._function_name = function_name
        self._arity = arity

    @abc.abstractmethod
    def call(self, interpreter: "Interpreter", arguments: List[LoxObject]) -> LoxObject:
        pass

    @property
    def arity(self) -> int:
        return self._arity


class ReturnState(Exception):
    def __init__(self, value: LoxObject) -> None:
        super(ReturnState, self).__init__()
        self.value = value


class LoxNil(LoxObject):
    def __init__(self) -> None:
        super(LoxNil, self).__init__()


LOX_TRUE = LoxBool(True)
LOX_FALSE = LoxBool(False)
LOX_NIL = LoxNil()


class LoxFunction(LoxCallable):
    def __init__(self, declaration: Function, closure: Environment, is_initializer: bool) -> None:
        super(LoxFunction, self).__init__(declaration.name.lexeme, len(declaration.params))
        self._declaration = declaration
        self._closure = closure
        self._is_initializer = is_initializer

    def call(self, interpreter: "Interpreter", arguments: List[LoxObject]) -> LoxObject:
        env = Environment(self._closure)
        for i, param in enumerate(self._declaration.params):
            env.define(param.lexeme, arguments[i])
        try:
            interpreter.execute_block(self._declaration.body, env)
        except ReturnState as ret:
            if self._is_initializer:
                return self._closure.get_at(0, "this")
            return ret.value
        if self._is_initializer:
            return self._closure.get_at(0, "this")
        return LOX_NIL

    def __str__(self) -> str:
        return f"<fn {self._function_name}>"

    def bind(self, instance: "LoxInstance") -> "LoxFunction":
        environment = Environment(self._closure)
        environment.define("this", instance)
        return LoxFunction(self._declaration, environment, self._is_initializer)


class LoxClass(LoxCallable):
    def __init__(
        self, name: str, superclass: Optional['LoxClass'], methods: Dict[str, LoxFunction]
    ) -> None:
        super(LoxClass, self).__init__(name, 0)
        self._name = name
        self._superclass = superclass
        self._methods = methods

    def call(self, interpreter: "Interpreter", arguments: List[LoxObject]) -> LoxObject:
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return f"Class {self._name}"

    def __repr__(self) -> str:
        return f"Class {self._name}"

    def find_method(self, name: str) -> Optional[LoxFunction]:
        method = self._methods.get(name)
        if method is not None:
            return method

        if self._superclass is not None:
            method = self._superclass.find_method(name)
        else:
            method = None
        return method

    @property
    def arity(self) -> int:
        initializer = self.find_method("init")
        if initializer is None:
            return 0
        return initializer.arity


class LoxInstance(LoxObject):
    def __init__(self, klass: LoxClass) -> None:
        super(LoxInstance, self).__init__()
        self._class = klass
        self._fields: Dict[str, LoxObject] = {}

    def __str__(self) -> str:
        return f"{self._class.name} instance"

    def get(self, name: Token) -> LoxObject:
        result = self._fields.get(name.lexeme)
        if result is not None:
            return result

        method = self._class.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise RuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: Token, value: LoxObject) -> None:
        self._fields[name.lexeme] = value
