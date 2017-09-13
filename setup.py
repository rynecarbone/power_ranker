# Follow these instructions to actually register this name
# http://python-packaging.readthedocs.io/en/latest/minimal.html
# https://tom-christie.github.io/articles/pypi/
# https://stackoverflow.com/questions/45207128/failed-to-upload-packages-to-pypi-410-gone

#from setuptools import setup
from distutils.core import setup

setup(name='power_ranker',
      version='0.0.1',
      description='Fantasy football power rankings for public ESPN leagues',
      url='http://github.com/rynecarbone/power_ranker',
      author='Ryne Carbone',
      author_email='ryne.carbone@gmail.com',
      license='MIT',
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
      ],
      packages=['power_ranker'],
      install_requires=[
        'requests',
        'numpy',
        'scipy',
        'matplotlib'
      ],
      scripts=[
        'bin/test-script'
      ],
      zip_safe=False)
