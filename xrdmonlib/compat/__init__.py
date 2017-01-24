"""
Compatibility for different Python versions
"""
# Python2
try:
    string_type = (str, unicode)
except NameError:
    string_type = (str,)

# Python2.6
try:
    from runpy import run_path
except ImportError:
    from ._runpy import run_path
