import pytest

from whodatbot.utils import TemplateFormatter


class Formatter(TemplateFormatter):

    required_fields = ('foo', 'bar')
    optional_fields = ('baz',)


@pytest.fixture
def formatter_class():
    return Formatter


@pytest.mark.parametrize('template,error', [
    ('test {foo} {bar:s}', 'format_spec is forbidden: bar'),
    ('test {foo!r} {bar}', 'conversion is forbidden: foo'),
    ('test {foo} {baz} {qux} {bar}', 'unexpected field: qux'),
    ('test {baz}', 'missing field(s): bar, foo'),
])
def test_invalid_template(formatter_class, template, error):
    with pytest.raises(ValueError) as excinfo:
        formatter_class(template)
    assert str(excinfo.value) == error


@pytest.mark.parametrize('template', [
    'test {foo} {bar} test',
    'test {bar} {foo} test',
    'test {bar} {foo} {baz} test',
])
def test_valid_template(formatter_class, template):
    formatter_class(template)


def test_partial_formatting(formatter_class):
    formatter = formatter_class('test1 {foo}{bar} test2')
    result = formatter(foo=123, baz='ignored')
    assert type(result) is str
    assert result == 'test1 123{bar} test2'


def test_partial_formatting_with_optional(formatter_class):
    formatter = formatter_class('test1 {foo}{bar} test2{baz}')
    result = formatter(foo=123, baz='VALUE')
    assert type(result) is str
    assert result == 'test1 123{bar} test2VALUE'


def test_full_formatting(formatter_class):
    formatter = formatter_class('test1 {foo}{bar} test2')
    result = formatter(foo=123, bar='BAR')
    assert type(result) is str
    assert result == 'test1 123BAR test2'


def test_full_formatting_with_optional(formatter_class):
    formatter = formatter_class('test1 {foo}{bar} test2{baz}')
    result = formatter(foo=123, bar='BAR', baz='VALUE')
    assert type(result) is str
    assert result == 'test1 123BAR test2VALUE'
