import operator
import re
from string import ascii_letters, digits
from typing import Callable, ClassVar, Dict, List, Pattern, Tuple, Union

BinaryOperator = Callable[[float, float], float]
BinaryOperators = Dict[str, BinaryOperator]
UnaryOperator = Callable[[float], float]
UnaryOperators = Dict[str, UnaryOperator]


class InvalidExpression(SyntaxError):
    pass


class InvalidIdentifier(SyntaxError):
    pass


class UnknownVariable(NameError):
    pass


class Calculator:
    """Smart Calculator

    description: https://hyperskill.org/projects/74

    P.S. NO `eval`
    """

    supported_operators: ClassVar[Pattern] = re.compile(r'\s*([-+/*^()=])\s*')

    precedence: ClassVar[Dict[str, int]] = {
        r'-': 1,
        r'+': 1,
        r'/': 2,
        r'*': 2,
        r'^': 3,
    }

    binary_operators: ClassVar[BinaryOperators] = {
        r'-': operator.sub,
        r'+': operator.add,
        r'/': operator.truediv,
        r'*': operator.mul,
        r'^': operator.pow,
    }
    unary_operators: ClassVar[UnaryOperators] = {
        r'-': operator.neg,
        r'+': operator.pos,
    }

    def __init__(self) -> None:
        self._variables: Dict[str, float] = dict()

    @staticmethod
    def help():
        print(
            "The program calculates string with addition '+', "
            "subtraction '-', multiplication '*', integer division '/' and"
            " power '^' binary operators and parentheses (...). "
            "It also support unary operators ('-', '+') before numbers."
            " Example:\n"
            ">  - -3-+- 8 *( ( 2^ 2 + 3 ^1)* 2 + 1) + - 6 / (3^3 - 8 *3 )"
            "\n121\n\nSupported commands:\n/help\n/variables"
        )

    def print_variables(self):
        print(
            *(f"{variable}: {value}" for variable, value in self._variables.items()),
            sep='\n',
        )

    def process_command(self, string: str) -> None:
        if string == '/help':
            self.help()
        elif string == '/variables':
            self.print_variables()
        else:
            print("Unknown command")

    @classmethod
    def remove_extra_spaces(cls, expression: str) -> str:
        """Removes spaces before and after binary_operators and
        at the beginning and at the end of the string
        """
        return re.sub(cls.supported_operators, r' \1 ', expression.strip())

    @classmethod
    def compute_postfix_expresion(
            cls, postfix_expression: List[Union[str, float]]
    ) -> float:
        stack: List[float] = list()
        for token in postfix_expression:
            if (
                    isinstance(token, str)
                    and token in cls.binary_operators
                    and len(stack) >= 2
            ):
                b: float = stack.pop()
                a: float = stack.pop()
                operator_: BinaryOperator = cls.binary_operators[token]
                stack.append(operator_(a, b))
            elif isinstance(token, int):
                stack.append(token)
            else:
                raise InvalidExpression
        # convert `float` result to `int` to pass tests on hyperskill.org
        if stack[-1] % 1 == 0:
            stack[-1] = int(stack[-1])
        return stack.pop()

    def transform_infix_to_postfix(
            self, infix_expression: List[str]
    ) -> List[Union[str, float]]:
        binary_operators_stack: List[str] = list()
        unary_operators_stack: List[str] = list()
        # `next_operator_is_binary` is used to catch unary operators
        # and two operand without operator
        next_operator_is_binary: bool = False

        postfix_expression: List[Union[str, float]] = list()
        for token in infix_expression:
            # binary operator
            if next_operator_is_binary and token in Calculator.binary_operators:
                while (
                        binary_operators_stack
                        and binary_operators_stack[-1] != r'('
                        and Calculator.precedence[token]
                        <= Calculator.precedence[binary_operators_stack[-1]]
                ):
                    postfix_expression.append(binary_operators_stack.pop())
                binary_operators_stack.append(token)
                # after one `binary operator` there can't be other `binary operator`
                next_operator_is_binary = False
            # unary operator
            elif token in Calculator.unary_operators and not next_operator_is_binary:
                unary_operators_stack.append(token)
            # number
            elif set(token).issubset(digits) and not next_operator_is_binary:
                number: float = int(token)
                # apply all `unary operators` to operand
                while unary_operators_stack:
                    operator_ = Calculator.unary_operators[unary_operators_stack.pop()]
                    number = operator_(number)
                postfix_expression.append(number)
                # after operand there can be only `binary operator`
                next_operator_is_binary = True
            # variable
            elif set(token).issubset(ascii_letters) and not next_operator_is_binary:
                if token not in self._variables:
                    raise UnknownVariable
                number = self._variables[token]
                while unary_operators_stack:
                    operator_ = Calculator.unary_operators[unary_operators_stack.pop()]
                    number = operator_(number)
                postfix_expression.append(number)
                next_operator_is_binary = True
            # parentheses
            elif token == r'(' and not next_operator_is_binary:
                # it is prohibited to use unary operators before parentheses
                if unary_operators_stack:
                    raise InvalidExpression
                binary_operators_stack.append(token)
            elif token == r')' and next_operator_is_binary:
                while binary_operators_stack and binary_operators_stack[-1] != r'(':
                    postfix_expression.append(binary_operators_stack.pop())
                else:
                    if not binary_operators_stack:
                        raise InvalidExpression
                binary_operators_stack.pop()  # pop '(' from stack
            # bad variable
            elif (set(token).intersection(ascii_letters)
                  and set(token).intersection(digits)):
                raise InvalidIdentifier
            # unknown
            else:
                raise InvalidExpression
        # pop all `binary operators` remain in stack
        while binary_operators_stack and binary_operators_stack[-1] != r'(':
            postfix_expression.append(binary_operators_stack.pop())
        else:
            if binary_operators_stack:
                raise InvalidExpression
        return postfix_expression

    def process_expression(self, expression: str) -> None:
        expression = self.remove_extra_spaces(expression)
        infix_expression: List[str] = expression.split()
        try:
            print(
                self.compute_postfix_expresion(
                    self.transform_infix_to_postfix(infix_expression)
                )
            )
        except InvalidExpression:
            print("Invalid expression")
        except UnknownVariable:
            print("Unknown variable")
        except InvalidIdentifier:
            print("Invalid identifier")

    def process_assignment(self, string: str) -> None:
        string = self.remove_extra_spaces(string)
        identifier, expression = string.split(' = ', 1)
        infix_expression: List[str] = expression.split()
        if set(identifier).issubset(ascii_letters):
            try:
                value: float = self.compute_postfix_expresion(
                    self.transform_infix_to_postfix(infix_expression)
                )
            except (InvalidExpression, InvalidIdentifier):
                print("Invalid assignment")
            except UnknownVariable:
                print("Unknown variable")
            else:
                self._variables[identifier] = value
        else:
            print("Invalid identifier")

    def run(self) -> None:
        input_string: str = input()
        while input_string != '/exit':
            if input_string.startswith('/'):  # is command
                self.process_command(input_string)
            elif '=' in input_string:  # is assignment
                self.process_assignment(input_string)
            elif input_string:
                self.process_expression(input_string)
            input_string = input()
        print("Bye!")


if __name__ == '__main__':
    calculator = Calculator()
    calculator.run()
