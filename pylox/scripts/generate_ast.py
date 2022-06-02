import sys
from typing import List, Tuple, TextIO


SYNTAX_TREE_TYPES = [
    ("Assign", "Assign a value to a variable.", [("Token", "name"), ("Expr", "value")]),
    ("Binary", "Binary operation.", [("Expr", "left"), ("Token", "operator"), ("Expr", "right")]),
    (
        "Call",
        "Call a function.",
        [("Expr", "callee"), ("Token", "paren"), ("List[Expr]", "arguments")],
    ),
    ("Get", "Get a property of an instance.", [("Expr", "instance"), ("Token", "name")]),
    ("Grouping", "Grouping of expressions.", [("Expr", "expression")]),
    ("Literal", "Literal value.", [("LoxObject", "value")]),
    ("Noop", "Null expression, does nothing.", []),
    (
        "Logical",
        "Logical expression.",
        [("Expr", "left"), ("Token", "operator"), ("Expr", "right")],
    ),
    (
        "Set",
        "Set a property on an object.",
        [("Expr", "instance"), ("Token", "name"), ("Expr", "value")],
    ),
    (
        "Super",
        "Get the base class/superclass of an object.",
        [("Token", "keyword"), ("Token", "method")],
    ),
    ("This", "Refer to an object inside its methods.", [("Token", "keyword")]),
    ("Unary", "Unary operation.", [("Token", "operator"), ("Expr", "right")]),
    ("Variable", "Variable access", [("Token", "name")]),
]

STATEMENT_TYPES = [
    ("Block", "Block of statements.", [("List[Stmt]", "statements")]),
    (
        "Class",
        "Class definition.",
        [
            ("Token", "name"),
            ("Optional[Variable]", "superclass"),
            ("List[\"Function\"]", "methods")
        ],
    ),
    ("Expression", "Expression statement.", [("Expr", "expression")]),
    (
        "Function",
        "Function definition.",
        [("Token", "name"), ("List[Token]", "params"), ("List[Stmt]", "body")],
    ),
    (
        "If",
        "If/else block.",
        [("Expr", "condition"), ("Stmt", "then_branch"), ("Stmt", "else_branch")],
    ),
    ("Null", "Null statement. Do nothing.", []),
    ("Print", "Print statement.", [("Expr", "expression")]),
    ("Return", "Return statement.", [("Token", "keyword"), ("Optional[Expr]", "value")]),
    ("Var", "Variable statement", [("Token", "name"), ("Expr", "initializer")]),
    ("While", "While loop.", [("Expr", "condition"), ("Stmt", "body")]),
]


TYPES = {"expr": SYNTAX_TREE_TYPES, "stmt": STATEMENT_TYPES}
BASE_NAMES = {"expr": "Expr", "stmt": "Stmt"}
MODULE_NAMES = {"expr": "expression", "stmt": "statement"}


def define_type(
    class_name: str, docstring: str, args: List[Tuple[str, str]], base_name: str, file: TextIO
) -> None:
    """Define a subtype."""
    file.write(f"class {class_name}({base_name}):\n")
    arg_list = ", ".join(f"{arg}: {arg_type}" for arg_type, arg in args)
    file.write(f"    def __init__(self, {arg_list}) -> None:\n")
    file.write(f"        \"\"\"{docstring}\"\"\"\n")
    file.write(f"        super({class_name}, self).__init__()\n")
    for arg_type, arg in args:
        file.write(f"        self._{arg} = {arg}\n")
    for arg_type, arg in args:
        file.write("\n")
        file.write("    @property\n")
        file.write(f"    def {arg}(self) -> {arg_type}:\n")
        file.write(f"        \"\"\"{arg.capitalize()}.\"\"\"\n")
        file.write(f"        return self._{arg}\n")
    file.write("\n")
    file.write("    def accept(self, visitor: \"Visitor[T]\") -> T:\n")
    file.write("        \"\"\"Call a visitor.\"\"\"\n")
    file.write(f"        return visitor.visit_{class_name.lower()}_{base_name.lower()}(self)\n")


def define_visitor(types: List[str], base_name: str, file: TextIO) -> None:
    """Define a visitor class."""
    file.write(f"class Visitor(abc.ABC, Generic[T]):\n")
    file.write("    \"\"\"Visitor class.\"\"\"\n")
    for class_type in types:
        file.write("\n")
        file.write("    @abc.abstractmethod\n")
        file.write(f"    def visit_{class_type.lower()}_{base_name.lower()}")
        file.write(f"(self, {base_name.lower()}: {class_type}) -> T:\n")
        file.write(f"        \"\"\"Visit class of type {class_type}.\"\"\"\n")


def generate_ast() -> None:
    if len(sys.argv) != 3:
        print("Usage: generate_ast.py <output_directory> <module>")
        exit(64)
    module = sys.argv[2]
    if module not in {"expr", "stmt"}:
        print("Available modules: expr, stmt")
        exit(64)
    output_dir = sys.argv[1]
    base_name = BASE_NAMES[module]
    module_name = MODULE_NAMES[module]
    module_types = TYPES[module]

    with open(f"{output_dir}/{module_name}.py", "w") as f:
        f.write("import abc\n")
        if module == "stmt":
            f.write("from typing import Generic, List, Optional, TypeVar\n")
            f.write("\n")
            f.write("from .expression import Expr, Variable\n")
            f.write("from .token import Token\n")
        elif module == "expr":
            f.write("from typing import Generic, List, TypeVar\n")
            f.write("\n")
            f.write("from .lox_object import LoxObject\n")
            f.write("from .token import Token\n")
        else:
            sys.stderr.write("Module must be stmt or expr")
            exit(-1)

        f.write("\n\n")
        f.write("T = TypeVar(\"T\")\n")
        f.write("\n\n")
        f.write(f"class {base_name}(abc.ABC):\n")
        f.write("    def __init__(self) -> None:\n")
        f.write(f"        \"\"\"Base type for all {module_name}s.\"\"\"\n")
        f.write("        pass\n")
        f.write("\n")
        f.write("    @abc.abstractmethod\n")
        f.write("    def accept(self, visitor: \"Visitor[T]\") -> T:\n")
        f.write("        \"\"\"Accept a visitor.\"\"\"\n")

        for class_name, docstring, args in module_types:
            f.write("\n\n")
            define_type(class_name, docstring, args, base_name, f)
        f.write("\n\n")
        define_visitor([class_name for class_name, _, _ in module_types], base_name, f)


if __name__ == "__main__":
    generate_ast()
