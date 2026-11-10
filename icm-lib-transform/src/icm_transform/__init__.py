"""Transform expressions: a function library, a pattern grammar and compiled pipelines.

``functions`` holds the functions an expression may call (``scale``, ``add``, ``sunssf``, ``sum_of`` ...), each
returning a convtools conversion with, where it has one, its ``inverse``. ``registry`` is where names resolve, and
where other packages add functions (the ``icm_transform.functions`` entry-point group). ``parser`` turns a pattern (a
dict of output fields to expressions) into a compiled pipeline over a whole message and reports which fields it reads.
``value`` compiles a transform of one value, as a driver applies to a point, with its inverse.
"""
from .functions import MISSING
from .parser import FieldMap, TransformParser, UnknownFunction, WILDCARD, expand_groups, path_matches
from .registry import Entry, RegistrationError, register
from .value import NotInvertible, ValueTransform, compile_value_transform

__all__ = ['Entry', 'FieldMap', 'MISSING', 'NotInvertible', 'RegistrationError', 'TransformParser', 'UnknownFunction', 'ValueTransform',
           'WILDCARD', 'compile_value_transform', 'expand_groups', 'path_matches', 'register']
