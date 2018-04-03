# using https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open('README.md', 'r') as readmefobj:
    long_desc = readmefobj.read()

setup(
    name='blackarrow',
    version='1.0.0',
    description='A fast keyword searcher',
    long_desc=long_desc,
    long_description_content_type='text/markdown',
    url='https://github.com/TheDataLeek/black-arrow',
    author='Zoe Farmer',
    author_email='zoe@dataleek.io',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',

    ]
)