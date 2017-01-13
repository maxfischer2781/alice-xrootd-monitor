"""
Compatibility for Python2/3
"""

try:
    string_type = (str, unicode)
except NameError:
    string_type = (unicode,)
