"""
Various helper utilities
"""
import os
import ast


def validate_process(pid, name=None):
    """
    Check whether there is a process with `pid` and `name`

    :param pid: pid of the running process
    :param name: name of the running process
    :type name: str or None
    :returns: whether there is a process with the given name and pid
    :rtype: bool
    """
    try:
        with open(os.path.join('/proc', str(pid), 'comm')) as proc_comm:
            proc_name = next(proc_comm).strip()
    except (OSError, IOError):
        return False
    return name is None or name == proc_name


def safe_eval(literal):
    """
    Attempt to evaluate a literal value

    Safely performs the evaluation of a literal. If the literal is not valid,
    it is assumed to be a regular string and returned unchanged.

    :param literal: literal to evaluate, e.g. `"1.0"` or `"{'foo': 3}"`
    :type literal: str
    :return: evaluated or original literal
    """
    try:
        return ast.literal_eval(literal)
    except (ValueError, SyntaxError):
        return literal
