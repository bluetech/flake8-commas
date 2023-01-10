from typing import Iterator
import os
import tokenize

from flake8_commas import get_comma_errors


C812 = 'C812 missing trailing comma'
C818 = 'C818 trailing comma on bare tuple prohibited'
C819 = 'C819 trailing comma prohibited'


def get_absolute_path(filepath: str) -> str:
    return os.path.join(os.path.dirname(__file__), filepath)


def get_tokens(filename: str) -> Iterator[tokenize.TokenInfo]:
    with tokenize.open(filename) as f:
        file_contents = f.readlines()
    file_contents_iter = iter(file_contents)

    def file_contents_next() -> str:
        return next(file_contents_iter)

    yield from tokenize.generate_tokens(file_contents_next)


def test_one_line_dict() -> None:
    filename = get_absolute_path('data/one_line_dict.py')
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_multiline_good_dict() -> None:
    filename = get_absolute_path('data/multiline_good_dict.py')
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_multiline_bad_dict() -> None:
    filename = get_absolute_path('data/multiline_bad_dict.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 14, 'line': 2, 'message': C812},
    ]


def test_bad_list() -> None:
    filename = get_absolute_path('data/bad_list.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 5, 'line': 4, 'message': C812},
        {'col': 5, 'line': 10, 'message': C812},
        {'col': 5, 'line': 17, 'message': C812},
    ]


def test_bad_function_call() -> None:
    filename = get_absolute_path('data/bad_function_call.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 17, 'line': 3, 'message': C812},
    ]


def test_multiline_bad_function_def() -> None:
    fixture = 'data/multiline_bad_function_def.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 13, 'line': 9, 'message': C812},
    ]


def test_bad_function_one_param() -> None:
    fixture = 'data/multiline_bad_function_one_param.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 13, 'line': 2, 'message': C812},
        {'col': 9, 'line': 8, 'message': C812},
    ]


def test_good_empty_comma_context() -> None:
    fixture = 'data/good_empty_comma_context.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_comma_good_dict() -> None:
    fixture = 'data/comment_good_dict.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_no_comma_required_list_comprehension() -> None:
    fixture = 'data/list_comprehension.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_no_comma_required_dict_comprehension() -> None:
    fixture = 'data/dict_comprehension.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_no_comma_required_multiline_if() -> None:
    fixture = 'data/multiline_if.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_no_comma_required_multiline_subscript() -> None:
    fixture = 'data/multiline_index_access.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 14, 'line': 27, 'message': C812},
        {'col': 14, 'line': 34, 'message': C812},
    ]


def test_comma_required_multiline_subscript_with_slice() -> None:
    fixture = 'data/multiline_subscript_slice.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 14, 'line': 5, 'message': C812},
        {'col': 14, 'line': 33, 'message': C812},
    ]


def test_comma_required_after_unpack_in_non_def_python_3_5() -> None:
    fixture = 'data/unpack.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 12, 'line': 4, 'message': C812},
        {'col': 9, 'line': 11, 'message': C812},
        {'col': 15, 'line': 19, 'message': C812},
        {'col': 12, 'line': 26, 'message': C812},
        {'col': 23, 'line': 32, 'message': C812},
        {'col': 14, 'line': 39, 'message': C812},
        {'col': 12, 'line': 46, 'message': C812},
        {'col': 12, 'line': 50, 'message': C812},
        {'col': 9, 'line': 58, 'message': C812},
        {'col': 9, 'line': 62, 'message': C812},
        {'col': 9, 'line': 68, 'message': C812},
        {'col': 12, 'line': 75, 'message': C812},
        {'col': 14, 'line': 83, 'message': C812},
        {'col': 19, 'line': 112, 'message': C812},
    ]


def test_no_comma_required_in_parenth_form() -> None:
    fixture = 'data/parenth_form.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_comma_required_in_argument_list() -> None:
    fixture = 'data/callable_before_parenth_form.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 7, 'line': 7, 'message': C812},
        {'col': 7, 'line': 15, 'message': C812},
        {'col': 7, 'line': 23, 'message': C812},
    ]


def test_comma_required_even_if_you_use_or() -> None:
    fixture = 'data/multiline_bad_or_dict.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 14, 'line': 3, 'message': C812},
    ]


def test_comma_not_required_even_if_you_use_dict_for() -> None:
    fixture = 'data/multiline_good_single_keyed_for_dict.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_comma_not_required_in_parenth_form_string_splits() -> None:
    fixture = 'data/multiline_string.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_comma_not_required_in_comment_lines() -> None:
    fixture = 'data/good_list.py'
    filename = get_absolute_path(fixture)
    assert list(get_comma_errors(get_tokens(filename))) == []


base = 'data/keyword_before_parenth_form/'


def test_base() -> None:
    filename = get_absolute_path(base + 'base.py')
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_base_bad() -> None:
    filename = get_absolute_path(base + 'base_bad.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
        {'col': 5, 'line': 2, 'message': C812},
        {'col': 10, 'line': 8, 'message': C812},
        {'col': 7, 'line': 14, 'message': C812},
        {'col': 11, 'line': 17, 'message': C812},
        {'col': 7, 'line': 21, 'message': C812},
        {'col': 11, 'line': 24, 'message': C812},
    ]


def test_py3() -> None:
    filename = get_absolute_path(base + 'py3.py')
    assert list(get_comma_errors(get_tokens(filename))) == []


def test_prohibited() -> None:
    filename = get_absolute_path('data/prohibited.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
       {'col': 21, 'line': 1, 'message': C819},
       {'col': 13, 'line': 3, 'message': C819},
       {'col': 18, 'line': 5, 'message': C819},
       {'col': 6, 'line': 10, 'message': C819},
       {'col': 21, 'line': 12, 'message': C819},
       {'col': 13, 'line': 14, 'message': C819},
       {'col': 18, 'line': 16, 'message': C819},
       {'col': 6, 'line': 21, 'message': C819},
       {'col': 10, 'line': 27, 'message': C819},
       {'col': 9, 'line': 29, 'message': C819},
    ]


def test_bare() -> None:
    # Tests inspired by flake8_tuple https://git.io/vxstN
    filename = get_absolute_path('data/bare.py')
    assert list(get_comma_errors(get_tokens(filename))) == [
       {'col': 8, 'line': 7, 'message': C818},
       {'col': 19, 'line': 9, 'message': C818},
       {'col': 8, 'line': 16, 'message': C818},
       {'col': 10, 'line': 20, 'message': C818},
       {'col': 32, 'line': 27, 'message': C818},
       {'col': 26, 'line': 29, 'message': C818},
       {'col': 17, 'line': 32, 'message': C818},
    ]
