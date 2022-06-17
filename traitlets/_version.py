import re

__version__ = "5.4.0.dev0"


# light version of the pep440 subset we use
# to build version_info tuple
_match = re.match(
    r"(\d+)+\.(\d+)\.(\d+)((?:(a|b|rc)\d+)|(?:\.dev\d+)|)$",
    __version__,
)
assert _match is not None, f"Invalid __version__: {__version__}"

_v = _match.groups()
version_info = tuple(int(_v[i]) for i in range(3))
if _v[3]:
    # item 3 is _any_ extra info on the end (pre, .post, etc.)
    version_info = version_info + (_v[3],)

print(version_info)
