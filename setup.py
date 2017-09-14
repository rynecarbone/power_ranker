from setuptools import setup
from setuptools import find_packages

setup(name='power_ranker',
      version='0.0.3',
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
      #packages=['power_ranker'],
      packages=find_packages(),
      include_package_data = True,
      install_requires=[
        'requests',
        'configparser',
        'numpy',
        'scipy',
        'matplotlib'
      ],
      python_requires='>=3',
      #package_data={'sample': ['package_data.dat'],},
      #scripts=['bin/test-script'],
      zip_safe=False)
