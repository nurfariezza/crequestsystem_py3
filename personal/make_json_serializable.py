# coding=utf-8
from json import JSONEncoder

# from http://stackoverflow.com/questions/18478287/making-object-json-serializable-with-regular-encoder
def _default(self, o):
    return getattr(o.__class__, 'tojson', _default.default)(o)

_default.default = JSONEncoder().default

JSONEncoder.default = _default