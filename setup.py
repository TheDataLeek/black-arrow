#!/usr/bin/env python
# using https://github.com/pypa/sampleproject/blob/master/setup.py

from os import path
from setuptools import setup, find_packages
from codecs import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as readmefobj:
    long_desc = readmefobj.read()

setup(
    name='blackarrow',
    version='1.0.8',
    description='A fast keyword searcher',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    url='https://github.com/TheDataLeek/black-arrow',
    author='Zoe Farmer',
    author_email='zoe@dataleek.io',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    keywords='development searching text find replace',
    packages=find_packages(exclude=['tests']),
    install_requires=['fabulous'],
    entry_points={
        'console_scripts': [
            'blackarrow=blackarrow:main',
            'ba=blackarrow:main'
        ]
    }
)
