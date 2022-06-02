from lox.ast_printer import AstPrinter
from lox.expression import Unary, Binary, Grouping, Literal
from lox.token import Token, TokenType

def main():
    expression = Binary(
        Unary(Token(TokenType.MINUS, "-", None, 1), Literal(123)),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67))
    )
    print(AstPrinter().print(expression))

if __name__ == "__main__":
    main()