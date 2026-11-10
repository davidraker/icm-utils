"""Tests for the transform expression language: patterns, repeated groups, stage input, parameters and functions."""

import pytest

from icm_transform.parser import TransformParser


@pytest.fixture
def parser():
    return TransformParser()


SUNSPEC_705 = {'705': {'Ena': 1, 'Crv': [
    {'ActPt': 2, 'VRef': 100, 'Pt': [{'V': 95, 'Var': 44}, {'V': 105, 'Var': -44}, {'V': 0, 'Var': 0}]},
    {'ActPt': 1, 'Pt': [{'V': 1, 'Var': 2}]}]}}


def test_flat_pattern_with_explicit_paths(parser):
    schema = {'foo': 'transform[bar](multiple(7), add(9))',
              'bar': 'transform[foo, 0](add(9), multiple(7))'}
    result = parser.build_transform_from_schema(schema).execute({'foo': [5, 6], 'bar': 4})
    assert result == {'foo': 37, 'bar': 98}


def test_omitted_path_uses_output_key(parser):
    # A bare string key must be treated as one path segment, not split into characters.
    result = parser.build_transform_from_schema({'foo': 'transform(add(1))'}).execute({'foo': 4})
    assert result == {'foo': 5}


def test_nested_groups_produce_nested_output(parser):
    schema = {'702': {'WMaxRtg': 'transform[DGEN, WMaxRtg]()',
                      'X': 'transform(multiple(2))'}}
    result = parser.build_transform_from_schema(schema).execute(
        {'DGEN': {'WMaxRtg': 5000}, '702': {'X': 21}})
    assert result == {'702': {'WMaxRtg': 5000, 'X': 42}}


def test_quoted_segments_accept_either_quote_style_and_special_characters(parser):
    schema = {'AI': {'22': "transform['DGEN', 'RegClas[1]']()",
                     '23': 'transform["DGEN", "DateTgt[Date]"]()'}}
    result = parser.build_transform_from_schema(schema).execute(
        {'DGEN': {'RegClas[1]': 7, 'DateTgt[Date]': 'd'}})
    assert result == {'AI': {'22': 7, '23': 'd'}}


def test_quoted_string_function_argument(parser):
    result = parser.build_transform_from_schema({'b': 'transform[x](cast_value("bool"))'}).execute({'x': 'yes'})
    assert result == {'b': True}


def test_null_pattern_values_are_skipped(parser):
    schema = {'DGEN': {'WMax': 'transform[a]()', 'Vmax': None}}
    result = parser.build_transform_from_schema(schema).execute({'a': 1})
    assert result == {'DGEN': {'WMax': 1}}


def test_unsupported_pattern_value_type_raises(parser):
    with pytest.raises(TypeError):
        parser.build_transform_from_schema({'a': 5})


def test_mean_ignores_missing_and_none(parser):
    schema = {'LNV': 'transform[PNV](mean(phsA.mag, phsB.mag, phsC.mag, phsD.mag))'}
    result = parser.build_transform_from_schema(schema).execute(
        {'PNV': {'phsA': {'mag': 120.0}, 'phsB': {'mag': 122.0}, 'phsC': {'mag': None}}})
    assert result == {'LNV': 121.0}


def test_list_of_patterns_is_chained(parser):
    chain = [{'a': 'transform[x](multiple(2))'}, {'b': 'transform[a](add(1))'}]
    assert parser.build_transform_from_schema(chain).execute({'x': 10}) == {'b': 21}


def test_missing_source_field_is_omitted_from_output(parser):
    schema = {'a': 'transform[x](multiple(2))', 'b': 'transform[y]()'}
    assert parser.build_transform_from_schema(schema).execute({'x': 3}) == {'a': 6}


def test_none_source_value_is_omitted_instead_of_raising(parser):
    """A device may publish a point with no value; a scaling transform must not raise on it (that dropped every other
    field of the message with it) but leave the field out."""
    schema = {'a': 'transform[x](multiple(2))', 'b': 'transform[y]()', 'c': 'transform[z](multiple(0.1))'}
    assert parser.build_transform_from_schema(schema).execute({'x': None, 'y': 5, 'z': 20}) == {'b': 5, 'c': 2.0}


def test_missing_source_handles_deep_paths_list_indices_and_scalar_parents(parser):
    schema = {'deep': 'transform[p, q, r]()',
              'idx': 'transform[AI, 5]()',
              'ok': 'transform[AI, 0]()',
              'scalar_parent': 'transform[n, q]()'}
    result = parser.build_transform_from_schema(schema).execute({'p': {}, 'AI': [1], 'n': 7})
    assert result == {'ok': 1}


def test_group_emptied_by_missing_fields_is_pruned(parser):
    schema = {'702': {'W': 'transform[DGEN, WMax]()', 'V': 'transform[DGEN, VMax]()'},
              '701': {'Hz': 'transform[MMXU, Hz]()'}}
    result = parser.build_transform_from_schema(schema).execute({'DGEN': {'WMax': 5}})
    assert result == {'702': {'W': 5}}


def test_none_value_is_present_not_missing(parser):
    assert parser.build_transform_from_schema({'a': 'transform[x]()'}).execute({'x': None}) == {'a': None}


def test_missing_fields_propagate_through_chain(parser):
    chain = [{'a': 'transform[x](multiple(2))', 'b': 'transform[y]()'},
             {'c': 'transform[a](add(1))', 'd': 'transform[b]()'}]
    assert parser.build_transform_from_schema(chain).execute({'x': 10}) == {'c': 21}


def test_repeated_group_iterates_marked_source_list(parser):
    schema = {'CurveData[#]': {'xvalue': 'transform[705, Crv, 0, Pt[#], V]()',
                               'yvalue': "transform[705, Crv, 0, 'Pt[#]', Var](multiple(10))"}}
    result = parser.build_transform_from_schema(schema).execute(SUNSPEC_705)
    assert result == {'CurveData': [{'xvalue': 95, 'yvalue': 440}, {'xvalue': 105, 'yvalue': -440},
                                    {'xvalue': 0, 'yvalue': 0}]}


def test_repeated_group_omitted_path_uses_output_keys(parser):
    schema = {'Crv[#]': {'ActPt': 'transform()', 'Pt[#]': {'V': 'transform()'}}}
    result = parser.build_transform_from_schema(schema).execute(SUNSPEC_705['705'])
    assert result == {'Crv': [{'ActPt': 2, 'Pt': [{'V': 95}, {'V': 105}, {'V': 0}]}, {'ActPt': 1, 'Pt': [{'V': 1}]}]}


def test_repeated_group_of_scalars(parser):
    schema = {'xs[#]': 'transform[705, Crv, 0, Pt[#], V]()'}
    assert parser.build_transform_from_schema(schema).execute(SUNSPEC_705) == {'xs': [95, 105, 0]}


def test_repeated_group_source_functions_and_take_by_path(parser):
    # A "#" entry without its own path applies functions to the implicitly named list. take() resolves
    # its path argument against the element enclosing the group (here the message root).
    schema = {'CurveData[#]': {'#': "transform(take('705.Crv.0.ActPt'))",
                               'xvalue': 'transform[705, Crv, 0, Pt[#], V]()'}}
    result = parser.build_transform_from_schema(schema).execute(SUNSPEC_705)
    assert result == {'CurveData': [{'xvalue': 95}, {'xvalue': 105}]}
    # Absent count field: list passes through untouched. Literal count: sliced.
    assert parser.build_transform_from_schema({'n[#]': {'#': "transform(take('nope'))", 'v': 'transform[705, Crv, 0, Pt[#], V]()'}}
                                              ).execute(SUNSPEC_705) == {'n': [{'v': 95}, {'v': 105}, {'v': 0}]}
    assert parser.build_transform_from_schema({'n[#]': {'#': 'transform(take(1))', 'v': 'transform[705, Crv, 0, Pt[#], V]()'}}
                                              ).execute(SUNSPEC_705) == {'n': [{'v': 95}]}


def test_repeated_group_explicit_source_with_as_list_and_count(parser):
    sep2 = {'DERCurve': {'opModVoltVar': {'vRef': 7, 'CurveData': [{'xvalue': 95, 'yvalue': 44}, {'xvalue': 105, 'yvalue': -44}]}}}
    schema = {'705': {'Crv[#]': {'#': 'transform[DERCurve, opModVoltVar](as_list())',
                                 'ActPt': 'transform[#, CurveData](count())',
                                 'VRef': 'transform[#, vRef]()',
                                 'Pt[#]': {'V': 'transform[#, CurveData[#], xvalue]()',
                                           'Var': 'transform[#, CurveData[#], yvalue]()'}}}}
    pipeline = parser.build_transform_from_schema(schema)
    assert pipeline.execute(sep2) == {'705': {'Crv': [{'ActPt': 2, 'VRef': 7,
                                                       'Pt': [{'V': 95, 'Var': 44}, {'V': 105, 'Var': -44}]}]}}
    assert pipeline.execute({'DERCurve': {}}) == {}


def test_nested_repeated_groups_and_enclosing_element_paths(parser):
    schema = {'curves[#]': {'act': 'transform[705, Crv[#], ActPt]()',
                            'ena': 'transform[705, Ena]()',                     # no marker: message root
                            'pts[#]': {'v': 'transform[705, Crv[#], Pt[#], V]()',
                                       'act': 'transform[705, Crv[#], ActPt]()'}}}  # one marker: the curve
    result = parser.build_transform_from_schema(schema).execute(SUNSPEC_705)
    assert result == {'curves': [{'act': 2, 'ena': 1, 'pts': [{'v': 95, 'act': 2}, {'v': 105, 'act': 2}, {'v': 0, 'act': 2}]},
                                 {'act': 1, 'ena': 1, 'pts': [{'v': 1, 'act': 1}]}]}


def test_repeated_group_missing_or_empty_list_is_omitted_and_empty_elements_dropped(parser):
    schema = {'ena': 'transform[705, Ena]()', 'pts[#]': {'v': 'transform[705, Crv, 0, Pt[#], V]()'}}
    pipeline = parser.build_transform_from_schema(schema)
    assert pipeline.execute({'705': {'Ena': 1}}) == {'ena': 1}
    assert pipeline.execute({'705': {'Ena': 1, 'Crv': [{'Pt': []}]}}) == {'ena': 1}
    assert pipeline.execute({'705': {'Ena': 1, 'Crv': [{'Pt': {'V': 1}}]}}) == {'ena': 1}          # not a list
    assert pipeline.execute({'705': {'Crv': [{'Pt': [{'V': 1}, {'Q': 3}]}]}}) == {'pts': [{'v': 1}]}


def test_paths_match_string_or_integer_keys(parser):
    pipeline = parser.build_transform_from_schema({'w': 'transform[701, W]()', 'ai': "transform[AI, '5']()"})
    assert pipeline.execute({'701': {'W': 1}, 'AI': {5: 2}}) == {'w': 1, 'ai': 2}
    assert pipeline.execute({701: {'W': 1}, 'AI': [0, 1, 2, 3, 4, 5]}) == {'w': 1}


def test_pairs_builds_points_from_flat_indexed_array(parser):
    schema = {'crvPts[#]': {'#': "transform[AO](pairs(249, 100, xVal, yVal), take('AO.246'))",
                            'xVal': 'transform[#, xVal]()', 'yVal': 'transform[#, yVal]()'}}
    ao = {'246': 2, '249': 1.0, '250': 2.0, '251': 3.0, '252': 4.0, '253': 0.0, '254': 0.0}
    assert parser.build_transform_from_schema(schema).execute({'AO': ao}) == {
        'crvPts': [{'xVal': 1.0, 'yVal': 2.0}, {'xVal': 3.0, 'yVal': 4.0}]}
    schema = {'p[#]': {'#': 'transform[AO](pairs(1, 3, x, y))', 'x': 'transform[#, x]()', 'y': 'transform[#, y]()'}}
    assert parser.build_transform_from_schema(schema).execute({'AO': [0, 5, 6, 7]}) == {'p': [{'x': 5, 'y': 6}, {'x': 7}]}


@pytest.mark.parametrize('schema, message', [
    ({'a': 'transform[705, Crv, 0, Pt[#], V]()'}, 'outside of a repeated group'),
    ({'a[#]': {'x': 'transform[705, Crv, 0, Pt[#], V]()', 'y': 'transform[706, Crv, 0, Pt[#], V]()'}}, 'disagree'),
    ({'a[#]': {'x': 'transform[705, Ena]()'}}, 'no source list'),
    ({'a[#]': {'#': 'transform[705, Crv]()', 'x': 'transform[705, Crv[#], ActPt]()'}}, 'must start with "#"'),
    ({'a[#]': {'x': 'transform[#, ActPt]()'}}, 'no "#" entry'),
    ({'a': {'#': 'transform[x]()'}}, 'only allowed directly inside a repeated group'),
    ({'[#]': {'x': 'transform[a[#], b]()'}}, 'Empty name'),
], ids=['stray-marker', 'disagreeing-lists', 'no-source', 'explicit-plus-named', 'bare-hash-no-source',
        'hash-outside-repeat', 'empty-name'])
def test_repeated_group_definition_errors(parser, schema, message):
    with pytest.raises(ValueError, match=message):
        parser.build_transform_from_schema(schema)


def test_root_stage_input_rebinds_the_message(parser):
    # The driver publishes devices/.../all as [values, meta]; device_values() yields the values dict and passes a
    # bare dict through, so one pattern serves both shapes. Root-relative paths ('/...') see the rebound input.
    schema = {'#': 'transform(device_values())',
              '701': {'W': "transform[701_W](scale_reg_pow_10('/701_W_SF'))", 'Hz': 'transform[701_Hz]()'}}
    pipeline = parser.build_transform_from_schema(schema)
    values = {'701_W': 98, '701_W_SF': 2, '701_Hz': 60}
    assert pipeline.execute([values, {'701_W': {'units': 'W'}}]) == {'701': {'W': 9800.0, 'Hz': 60}}
    assert pipeline.execute(values) == {'701': {'W': 9800.0, 'Hz': 60}}
    # Without the directive the list yields nothing, which is the failure the directive exists to prevent.
    assert parser.build_transform_from_schema({'701': {'Hz': 'transform[701_Hz]()'}}).execute([values, {}]) == {}
    # Any expression may rebind the input; a chain applies each stage's rebind to that stage's input only.
    chain = [{'#': 'transform[payload]()', 'a': 'transform[x]()'}, {'b': 'transform[a](add(1))'}]
    assert parser.build_transform_from_schema(chain).execute({'payload': {'x': 1}}) == {'b': 2}
    with pytest.raises(TypeError):
        parser.build_transform_from_schema({'#': 5, 'a': 'transform[x]()'})


def test_root_stage_input_is_ignored_by_the_field_map(parser):
    field_map = parser.field_map({'#': 'transform(device_values())', '701': {'W': 'transform[701_W]()'}})
    assert field_map.sources() == {('701_W',)} and field_map.targets() == {('701', 'W')}


def test_parameters_and_generated_header_values(parser):
    # param() binds per-resource values when the chain is compiled; uuid4() and timestamp() are produced per message.
    schema = {'header': {'mRID': 'uuid4()', 'stamp': 'timestamp()'},
              'device': {'mRID': "param('mrid')", 'name': "param('name')"},
              'body': 'transform[essReading]()'}
    bound = TransformParser(context={'mrid': 'dev-1'}).build_transform_from_schema(schema)
    first, second = bound.execute({'essReading': {'W': 1}}), bound.execute({'essReading': {'W': 1}})
    assert first['device'] == {'mRID': 'dev-1'} and first['body'] == {'W': 1}          # unbound 'name' is dropped
    assert first['header']['mRID'] != second['header']['mRID'] and len(first['header']['mRID']) == 36
    assert set(first['header']['stamp']) == {'seconds', 'nanoseconds'} and first['header']['stamp']['seconds'] > 1_700_000_000
    assert 'device' not in parser.build_transform_from_schema(schema).execute({'essReading': {}})   # no context at all
    # Generated values carry nothing from the source, so they weigh nothing in the field map.
    field_map = parser.field_map(schema)
    assert {m.target: m.fidelity for m in field_map.mappings} == {
        ('header', 'mRID'): 0.0, ('header', 'stamp'): 0.0, ('device', 'mRID'): 0.0, ('device', 'name'): 0.0, ('body',): 1.0}


def test_repeated_group_element_source_wraps_enclosing_element(parser):
    # "#" with functions only and no list named by the siblings: the enclosing element is the source.
    schema = {'705': {'Crv[#]': {'#': 'transform(as_list())', 'VRef': 'transform[AI, 29]()', 'RspTms': 'transform[AI, 298]()'}}}
    pipeline = parser.build_transform_from_schema(schema)
    assert pipeline.execute({'AI': {'29': 100, '298': 5}}) == {'705': {'Crv': [{'VRef': 100, 'RspTms': 5}]}}
    assert pipeline.execute({'AI': {'1': 1}}) == {}


def test_leading_hash_refers_to_innermost_group_element(parser):
    # Inside Pt[#] (level 2) a path starting with "#" means the point, even though Crv[#] also uses "#".
    schema = {'Crv[#]': {'#': 'transform(as_list())', 'ActPt': 'transform[AI, 330]()',
                         'Pt[#]': {'#': 'transform[AI](pairs(333, 100, V, Var))',
                                   'V': 'transform[#, V]()', 'Var': 'transform[#, Var]()'}}}
    result = parser.build_transform_from_schema(schema).execute({'AI': {'330': 1, '333': 9, '334': 8}})
    assert result == {'Crv': [{'ActPt': 1, 'Pt': [{'V': 9, 'Var': 8}]}]}
    # A path with two markers written inside the inner group reaches both levels.
    schema = {'Crv[#]': {'#': 'transform[DERCurve, opModVoltVar](as_list())',
                         'Pt[#]': {'V': 'transform[#, CurveData[#], xvalue]()'}}}
    result = parser.build_transform_from_schema(schema).execute({'DERCurve': {'opModVoltVar': {'CurveData': [{'xvalue': 3}]}}})
    assert result == {'Crv': [{'Pt': [{'V': 3}]}]}
    with pytest.raises(ValueError, match='some paths start with "#"'):
        parser.build_transform_from_schema({'a[#]': {'x': 'transform[705, Crv, 0, Pt[#], V]()', 'y': 'transform[#, V]()'}})


def test_labelled_repeated_groups_concatenate_into_one_list(parser):
    schema = {'sequence[#] first': {'#': 'transform[a](as_list())', 'v': 'transform[#, x]()'},
              'sequence[#] second': {'#': 'transform[b](as_list())', 'v': 'transform[#, x](multiple(10))'}}
    pipeline = parser.build_transform_from_schema(schema)
    assert pipeline.execute({'a': {'x': 1}, 'b': {'x': 2}}) == {'sequence': [{'v': 1}, {'v': 20}]}
    assert pipeline.execute({'b': {'x': 2}}) == {'sequence': [{'v': 20}]}
    assert pipeline.execute({}) == {}
    with pytest.raises(ValueError, match='both as a field and as a repeated group'):
        parser.build_transform_from_schema({'s': 'transform[x]()', 's[#]': {'v': 'transform[y[#]]()'}})


def test_spread_entries_merge_groups_in_position(parser):
    schema = {'g': {'k': 'transform[x]()', '*more': 'transform[y]()', 'z': 'transform[x]()'}}
    result = parser.build_transform_from_schema(schema).execute({'x': 1, 'y': {'a': 2, 'b': 3}})
    assert list(result['g'].items()) == [('k', 1), ('a', 2), ('b', 3), ('z', 1)]
    assert parser.build_transform_from_schema(schema).execute({'x': 1}) == {'g': {'k': 1, 'z': 1}}
    # A spread that does not produce a group contributes nothing.
    assert parser.build_transform_from_schema({'g': {'*s': 'transform[x](const(5))'}}).execute({'x': 1}) == {}
    with pytest.raises(TypeError):
        parser.build_transform_from_schema({'g': {'*s': {'a': 'transform[x]()'}}})


def test_guards_and_const(parser):
    pipeline = parser.build_transform_from_schema({'v': "transform[x](when('mode', 2), multiple(10))",
                                                   'w': "transform[x](when_equal('sel', 'idx'))",
                                                   'c': 'transform[x](const(7))'})
    assert pipeline.execute({'x': 4, 'mode': 2.0, 'sel': 1, 'idx': 1}) == {'v': 40, 'w': 4, 'c': 7}
    assert pipeline.execute({'x': 4, 'mode': 3, 'sel': 1}) == {'c': 7}        # guard false; idx absent
    assert pipeline.execute({'mode': 2}) == {}                                # source absent: const not emitted


def test_unpairs_lays_points_out_as_numbered_values(parser):
    schema = {'AO': {'246': 'transform[pts](count())', '*points': 'transform[pts](unpairs(249, x, y))', '217': 'transform[pts](const(1))'}}
    result = parser.build_transform_from_schema(schema).execute({'pts': [{'x': 95, 'y': 44}, {'x': 105}]})
    assert list(result['AO'].items()) == [('246', 2), ('249', 95), ('250', 44), ('251', 105), ('217', 1)]


# ---- modbus_tk style register transforms ----

def test_numeric_literals_may_be_signed_or_fractional(parser):
    pipeline = parser.build_transform_from_schema({'a': 'transform[x](multiple(0.5))', 'b': 'transform[x](add(-3))',
                                                   'c': 'transform[x](multiple(1e-3))'})
    assert pipeline.execute({'x': 10}) == {'a': 5.0, 'b': 7, 'c': 0.01}


def test_scale_fixes_decimal_noise_and_inverts(parser):
    from icm_transform import functions as transforms
    assert parser.build_transform_from_schema({'v': 'transform[x](scale(0.001))'}).execute({'x': 12345}) == {'v': 12.345}
    assert 3 * 0.1 != 0.3                   # the noise scale() removes
    assert transforms.scale(0.1).execute(3) == 0.3
    conv = transforms.scale('0.001')          # string arguments as in the modbus_tk register maps
    assert conv.execute(12345) == 12.345
    assert conv.inverse.execute(12.345) == 12345.0
    assert transforms.scale(0).inverse.execute(5) is None
    assert transforms.scale(2).inverse.execute('abc') == 'abc'


def test_scale_reg_and_scale_reg_pow_10_use_a_sibling_register(parser):
    from icm_transform import functions as transforms
    schema = {'W': "transform[701, W](scale_reg_pow_10('701.W_SF'))",
              'V': "transform[701, V](scale_reg('701.V_DIV'))"}
    pipeline = parser.build_transform_from_schema(schema)
    assert pipeline.execute({'701': {'W': 12345, 'W_SF': -1, 'V': 2400, 'V_DIV': 10}}) == {'W': 1234.5, 'V': 240.0}
    assert pipeline.execute({'701': {'W': 12345, 'W_SF': 2, 'V': 240}}) == {'W': 1234500.0, 'V': 240}   # V_DIV absent: V unchanged
    assert pipeline.execute({'701': {'W': 5, 'V': 2400, 'V_DIV': 0}}) == {'W': 5, 'V': None}    # W_SF absent: unchanged; /0 -> None
    # Inside a repeated group the register path is relative to the element.
    schema = {'pts[#]': {'v': "transform[705, Crv, 0, Pt[#], V](scale_reg_pow_10('sf'))"}}
    assert parser.build_transform_from_schema(schema).execute(
        {'705': {'Crv': [{'Pt': [{'V': 950, 'sf': -1}, {'V': 1050, 'sf': -1}]}]}}) == {'pts': [{'v': 95.0}, {'v': 105.0}]}
    # Inverses need the register too; they read it from the same enclosing element (labelled each0 at top level).
    from convtools import conversion as c
    def invert(conv, element, value):
        return c.this.pipe(c.naive(value).pipe(conv.inverse), label_input='each0').execute(element)
    assert invert(transforms.scale_reg_pow_10('sf'), {'sf': -1}, 95.0) == 950.0
    assert invert(transforms.scale_reg('d'), {'d': 10}, 240.0) == 2400.0
    assert invert(transforms.scale_reg('d'), {}, 240.0) == 240.0                       # absent register: unchanged


def test_no_op_copies_and_is_its_own_inverse():
    from icm_transform import functions as transforms
    conv = transforms.no_op()
    assert conv.execute({'a': 1}) == {'a': 1} and conv.inverse.execute(7) == 7


@pytest.mark.parametrize('name, reverse, registers, expected', [
    # registers listed from the highest 16 bits of the packed integer to the lowest; values follow modbus_tk
    ('mod10k', False, [12, 3456], 12 * 10000 + 3456),
    ('mod10k', True, [12, 3456], 3456 * 10000 + 12),
    ('mod10k64', False, [4, 3, 2, 1], 1 * 10000 ** 3 + 2 * 10000 ** 2 + 3 * 10000 + 4),
    ('mod10k64', True, [4, 3, 2, 1], 4 * 10000 ** 3 + 3 * 10000 ** 2 + 2 * 10000 + 1),
    ('mod10k48', False, [4, 3, 2, 1], 2 * 10000 ** 2 + 3 * 10000 + 4),
    ('mod10k48', True, [4, 3, 2, 1], 1 * 10000 ** 2 + 2 * 10000 + 3),
])
def test_mod10k_family_matches_modbus_tk(parser, name, reverse, registers, expected):
    from icm_transform import functions as transforms
    packed = 0
    for word in registers:
        packed = (packed << 16) | word
    conv = getattr(transforms, name)(reverse)
    assert conv.execute(packed) == expected
    assert parser.build_transform_from_schema({'v': f'transform[x]({name}({"True" if reverse else "False"}))'}
                                              ).execute({'x': packed}) == {'v': expected}
    # The inverse packs the digit groups back into the registers the value came from.
    repacked = conv.inverse.execute(expected)
    used = {'mod10k': [1, 0], 'mod10k64': [0, 1, 2, 3], 'mod10k48': [1, 2, 3] if not reverse else [0, 1, 2]}[name]
    for index in used:
        assert (repacked >> (16 * index)) & 0xFFFF == (packed >> (16 * index)) & 0xFFFF


def test_all_null_repeated_group_is_skipped(parser):
    schema = {'705': {'Crv[#]': {'Pt[#]': {'V': None}}}, 'x': 'transform[a]()'}
    assert parser.build_transform_from_schema(schema).execute({'a': 1}) == {'x': 1}


