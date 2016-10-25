from distutils.core import setup


setup(
  name='eegtools',
  url='https://github.com/breuderink/eegtools',
  author='Boris Reuderink',
  author_email='b.reuderink@gmail.com',
  license='New BSD',
  version='0.2.1',
  install_requires=open('requirements.in').readlines(),
  tests_require=open('requirements.testing.in').readlines(),
  packages=['eegtools', 'eegtools.io', 'eegtools.data'],
)
