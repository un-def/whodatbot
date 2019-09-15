import argparse
import os

import pytest

from whodatbot.cli import StoreEnvVarAction


ENVVAR = 'OPT_ENVVAR'


@pytest.fixture
def parser(request):
    parser = argparse.ArgumentParser()
    parser.register('action', 'store_envvar', StoreEnvVarAction)
    marker = request.node.get_closest_marker('add_argument')
    if marker:
        parser.add_argument(
            '--opt', action='store_envvar', envvar=ENVVAR, **marker.kwargs)
    return parser


@pytest.mark.add_argument
def test_not_required_no_arg_no_envvar_no_default(parser):
    namespace = parser.parse_args([])
    assert namespace.opt is None


@pytest.mark.add_argument(default='def')
def test_not_required_no_arg_no_envvar_with_default(parser):
    namespace = parser.parse_args([])
    assert namespace.opt == 'def'


@pytest.mark.parametrize('', [
    pytest.param(marks=pytest.mark.add_argument(required=True)),
    pytest.param(marks=pytest.mark.add_argument(required=True, default='def')),
])
def test_required_no_arg_with_envvar(monkeypatch, parser):
    monkeypatch.setitem(os.environ, ENVVAR, 'env')
    namespace = parser.parse_args([])
    assert namespace.opt == 'env'


@pytest.mark.parametrize('with_envvar', [False, True])
@pytest.mark.parametrize('', [
    pytest.param(marks=pytest.mark.add_argument(required=True)),
    pytest.param(marks=pytest.mark.add_argument(required=True, default='def')),
])
def test_required_with_arg(monkeypatch, parser, with_envvar):
    if with_envvar:
        monkeypatch.setitem(os.environ, ENVVAR, 'env')
    namespace = parser.parse_args(['--opt', 'arg'])
    assert namespace.opt == 'arg'


@pytest.mark.add_argument(required=True)
def test_required_no_arg_no_envvar(parser):
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args([])
    assert excinfo.value.code != 0
