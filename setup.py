from distutils.core import setup

version = '0.0.2'

setup(
    name='traitlets',
    version=version,
    author='IPython dev team',
    url='https://github.com/ipython/traitlets',
    packages=['traitlets',],
    license='BSD',
    long_description=open('README.md').read(),
)
