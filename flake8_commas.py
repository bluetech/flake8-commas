from typing import Iterator, TypedDict
import collections
import dataclasses
import enum
import tokenize


# A parenthesized expression list yields whatever that expression list
# yields: if the list contains at least one comma, it yields a tuple;
# otherwise, it yields the single expression that makes up the expression
# list.

PYTHON_KWDS = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'break', 'class',
    'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for',
    'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
    'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
}
# treat import like a function, not a keyword.
ALL_KWDS = PYTHON_KWDS - {'import'}


class Comma(enum.Enum):
    NO = 'no'
    # Tuple-like item list.
    TUPLE = 'tuple-or-parenth-form'
    # Subscript item list.
    SUBSCRIPT = 'subscript'
    # List-like item list.
    LIST = 'list'
    # Dict-/set-like item list.
    DICT = 'dict'
    # Lambda parameter list.
    LAMBDA_PARAMETERS = 'lambda-parameters'
    # Function definition parameter list.
    FUNCTION_PARAMETERS = 'function-parameters'
    # Call argument-like item list.
    CALL_ARGUMENTS = 'argument-list'

    def is_always_allowed(self) -> bool:
        return self in (
            Comma.LIST,
            Comma.DICT,
            Comma.FUNCTION_PARAMETERS,
            Comma.CALL_ARGUMENTS,
        )

    def is_tupleish(self) -> bool:
        return self in (
            Comma.SUBSCRIPT,
            Comma.TUPLE,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Context:
    comma: Comma
    # Number of commas.
    n: int = 0


class TokenType(enum.Enum):
    NL = 'nl'
    NEWLINE = 'newline'
    COMMA = ','
    OPENING_BRACKET = '('
    OPENING_SQUARE_BRACKET = '['
    OPENING_CURLY_BRACKET = '{'
    SOME_CLOSING = 'some-closing'
    FOR = 'for'
    NAMED = 'named'
    DEF = 'def'
    LAMBDA = 'lambda'
    COLON = ':'


@dataclasses.dataclass(frozen=True, slots=True)
class Token:
    """Simplified token type specialized for the task."""
    info: tokenize.TokenInfo | None
    type: TokenType | None

    @classmethod
    def none(cls) -> 'Token':
        return cls(info=None, type=None)

    @classmethod
    def from_token(cls, token: tokenize.TokenInfo) -> 'Token':
        if token.type == tokenize.NL:
            type = TokenType.NL
        elif token.type == tokenize.NEWLINE:
            type = TokenType.NEWLINE
        elif token.type == tokenize.NAME and token.string == 'for':
            type = TokenType.FOR
        elif token.type == tokenize.NAME and token.string == 'def':
            type = TokenType.DEF
        elif token.type == tokenize.NAME and token.string == 'lambda':
            type = TokenType.LAMBDA
        elif token.type == tokenize.NAME and token.string not in ALL_KWDS:
            type = TokenType.NAMED
        elif token.string == ',':
            type = TokenType.COMMA
        elif token.string == '(':
            type = TokenType.OPENING_BRACKET
        elif token.string == '[':
            type = TokenType.OPENING_SQUARE_BRACKET
        elif token.string in ('[', '{'):
            type = TokenType.OPENING_CURLY_BRACKET
        elif token.string in (']', ')', '}'):
            type = TokenType.SOME_CLOSING
        elif token.string == ':':
            type = TokenType.COLON
        else:
            type = None
        return cls(info=token, type=type)

    def is_opening(self) -> bool:
        return self.type in (
            TokenType.OPENING_BRACKET,
            TokenType.OPENING_SQUARE_BRACKET,
            TokenType.OPENING_CURLY_BRACKET,
        )


def simple_tokens(
    file_tokens: Iterator[tokenize.TokenInfo],
) -> Iterator[Token]:
    tokens = (
        Token.from_token(t) for t in file_tokens if t.type != tokenize.COMMENT
    )

    token = next(tokens)
    for next_token in tokens:
        if token.type is TokenType.NL and next_token.type is TokenType.NL:
            continue
        yield token
        token = next_token


class Error(TypedDict):
    message: str
    line: int
    col: int


def get_comma_errors(
    file_tokens: Iterator[tokenize.TokenInfo],
) -> Iterator[Error]:
    tokens = simple_tokens(file_tokens)

    stack = [Context(Comma.NO)]

    window = collections.deque([Token.none(), Token.none()], maxlen=3)

    for token in tokens:
        window.append(token)
        prev_prev, prev, _ = window
        if token.is_opening():
            if token.type is TokenType.OPENING_BRACKET:
                if prev.type in (TokenType.SOME_CLOSING, TokenType.NAMED):
                    if prev_prev.type is TokenType.DEF:
                        stack.append(Context(Comma.FUNCTION_PARAMETERS))
                    else:
                        stack.append(Context(Comma.CALL_ARGUMENTS))
                else:
                    stack.append(Context(Comma.TUPLE))

            elif token.type is TokenType.OPENING_SQUARE_BRACKET:
                if prev.type in (TokenType.SOME_CLOSING, TokenType.NAMED):
                    stack.append(Context(Comma.SUBSCRIPT))
                else:
                    stack.append(Context(Comma.LIST))

            else:
                stack.append(Context(Comma.DICT))

        elif token.type is TokenType.LAMBDA:
            stack.append(Context(Comma.LAMBDA_PARAMETERS))

        elif token.type is TokenType.FOR:
            stack[-1] = Context(Comma.NO)

        elif token.type is TokenType.COMMA:
            stack[-1] = dataclasses.replace(stack[-1], n=stack[-1].n + 1)

        comma_allowed = token.type is TokenType.SOME_CLOSING and (
            stack[-1].comma.is_always_allowed()
            or stack[-1].comma.is_tupleish() and stack[-1].n >= 1
        )

        comma_prohibited = prev.type is TokenType.COMMA and (
            (
                comma_allowed
                and (not stack[-1].comma.is_tupleish() or stack[-1].n > 1)
            ) or (
                stack[-1].comma is Comma.LAMBDA_PARAMETERS
                and token.type is TokenType.COLON
            )
        )
        if comma_prohibited:
            assert prev.info is not None
            end_row, end_col = prev.info.end
            yield Error(
                message='C819 trailing comma prohibited',
                line=end_row,
                col=end_col,
            )

        bare_comma_prohibited = (
            token.type is TokenType.NEWLINE
            and prev.type is TokenType.COMMA
        )
        if bare_comma_prohibited:
            assert prev.info is not None
            end_row, end_col = prev.info.end
            yield Error(
                message='C818 trailing comma on bare tuple prohibited',
                line=end_row,
                col=end_col,
            )

        comma_required = (
            comma_allowed
            and prev.type is TokenType.NL
            and prev_prev.type is not TokenType.COMMA
            and not prev_prev.is_opening()
        )
        if comma_required:
            assert prev_prev.info is not None
            end_row, end_col = prev_prev.info.end
            yield Error(
                message='C812 missing trailing comma',
                line=end_row,
                col=end_col,
            )

        pop_stack = token.type is TokenType.SOME_CLOSING or (
            token.type is TokenType.COLON
            and stack[-1].comma is Comma.LAMBDA_PARAMETERS
        )
        if pop_stack:
            stack.pop()


class CommaChecker:
    def __init__(
        self,
        tree: object,
        filename: str,
        file_tokens: Iterator[tokenize.TokenInfo],
    ) -> None:
        self.filename = filename
        self.tokens = file_tokens

    def run(self) -> Iterator[object]:
        for error in get_comma_errors(self.tokens):
            yield (error['line'], error['col'], error['message'], type(self))
