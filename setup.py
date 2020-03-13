#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2017, Zebula Sampedro, CU Boulder Research Computing.
# Distributed under the terms of the Modified BSD License.

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import os
import sys

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

# Get the current package version.
version_ns = {}
with open(pjoin(here, 'version.py')) as f:
    exec(f.read(), {}, version_ns)

setup_args = dict(
    name                = 'jupyterhub-singularity',
    packages            = ['jupyterhub-singularity'],
    version             = version_ns['__version__'],
    description         = """Singularity Spawner: Spawn Jupyter Notebooks that run inside Singularity containers.""",
    long_description    = "",
    author              = "yftian",
    author_email        = "642209942@qq.com",
    url                 = "https://github.com/yftian/jupyterhub-singularity",
    license             = "BSD",
    platforms           = "Linux",
    keywords            = ['Interactive', 'Interpreter', 'Shell', 'Web', 'Singularity', 'Containers'],
    classifiers         = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)

# setuptools requirements
if 'setuptools' in sys.modules:
    setup_args['install_requires'] = install_requires = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith(('-e', '#')):
                continue
            install_requires.append(req)


def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
