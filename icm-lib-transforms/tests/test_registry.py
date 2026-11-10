"""Tests for the function registry: built-ins, aliases, extensions and entry points."""
import pytest
from convtools import conversion as c

from icm.transforms import RegistrationError, TransformParser, UnknownFunction, compile_value_transform, register
from icm.transforms import registry, value


def _forget(*names):
    for n in names:
        registry._REGISTRY.pop(n, None)
    value._compile.cache_clear()


def test_every_builtin_is_registered_with_its_metadata():
    names = registry.names(aliases=False)
    for name in ('scale', 'scale_reg', 'sunssf', 'sum_of', 'equals', 'map', 'not', 'round', 'bool', 'literal', 'reg_name'):
        assert name in names
    assert registry.get('scale_int').fidelity == 0.9 and registry.get('scale_int').result_type is int
    assert registry.get('sum_of').fidelity == 0.0 and registry.get('all_equal_of').result_type is bool
    assert registry.get('scope') is None and registry.get('_numeric') is None      # helpers are not functions


def test_aliases_resolve_to_the_same_entry():
    assert registry.get('eq') is registry.get('equals') and registry.get('eq').name == 'equals'
    assert registry.get('lt').name == 'less_than' and 'lt' in registry.get('less_than').aliases
    assert 'lt' in registry.names() and 'lt' not in registry.names(aliases=False)


def test_unknown_function_is_an_error_naming_the_function_and_the_field():
    with pytest.raises(UnknownFunction) as e:
        TransformParser().build_transform_from_schema({'X': 'transform[705, Ena](no_such_function())'})
    assert e.value.name == 'no_such_function' and e.value.where == 'X'


def _double():
    conv = c.this * 2
    conv.inverse = c.this / 2
    return conv


def test_registered_extension_is_usable_in_patterns_and_value_transforms():
    register('test_double', _double, aliases=('dbl',), result_type=float)
    try:
        assert compile_value_transform('dbl()').forward(4) == 8 and compile_value_transform('dbl()').functions == ('test_double',)
        assert compile_value_transform('test_double()').result_type is float and compile_value_transform('test_double()').fidelity == 1.0
        assert TransformParser().build_transform_from_schema({'y': 'transform[x](test_double())'}).execute({'x': 3}) == {'y': 6}
    finally:
        _forget('test_double', 'dbl')


def test_same_factory_again_is_fine_but_a_different_one_under_a_taken_name_is_not():
    register('test_twice', _double)
    try:
        register('test_twice', _double)
        with pytest.raises(RegistrationError, match='already registered'):
            register('test_twice', lambda: c.this)
        with pytest.raises(RegistrationError):
            register('test_other', lambda: c.this, aliases=('scale',))      # an alias may not shadow a built-in either
    finally:
        _forget('test_twice', 'test_other')


def test_entry_points_add_functions_from_other_packages(monkeypatch):
    class FakeEntryPoint:
        def __init__(self, name, obj, dist='other-package'):
            self.name, self._obj, self.value = name, obj, f'{dist}.transforms:{name}'
            self.dist = type('Dist', (), {'name': dist})()

        def load(self):
            if isinstance(self._obj, Exception):
                raise self._obj
            return self._obj

    def triple():
        return c.this * 3

    eps = [FakeEntryPoint('test_triple', triple), FakeEntryPoint('test_bundle', {'test_quad': lambda: c.this * 4}),
           FakeEntryPoint('test_broken', ImportError('no such module'))]
    monkeypatch.setattr(registry.metadata, 'entry_points', lambda group: eps if group == registry.ENTRY_POINT_GROUP else [])
    try:
        registry.load_entry_points(force=True)
        assert registry.get('test_triple').package == 'other-package' and registry.get('test_quad') is not None
        assert registry.get('test_broken') is None                                   # a broken plugin is skipped, not fatal
        assert compile_value_transform('test_triple()').forward(2) == 6
    finally:
        _forget('test_triple', 'test_quad')
