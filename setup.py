#!/usr/bin/env python
import os
from setuptools import setup, find_packages

repo_base_dir = os.path.abspath(os.path.dirname(__file__))
# pull in the packages metadata
package_about = {}
with open(os.path.join(repo_base_dir, "xrdmon", "__about__.py")) as about_file:
    exec(about_file.read(), package_about)

if __name__ == '__main__':
    setup(
        name=package_about['__title__'],
        version=package_about['__version__'],
        descriptions=package_about['__summary__'],
        author=package_about['__author__'],
        author_email=package_about['__email__'],
        url=package_about['__uri__'],
        packages=find_packages(),
        # dependencies
        # TODO: switch this to a pypi source once available
        dependency_links=['http://monalisa.caltech.edu/download/apmon/ApMon_py_2.20.tgz#egg=apmon-2.2.20'],
        install_requires=['apmon'],
    )
