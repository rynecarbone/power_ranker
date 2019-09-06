from setuptools import setup
from setuptools import find_packages

setup(name='power_ranker',
      version='1.1.1',
      description='Fantasy football power rankings for public ESPN leagues',
      long_description=open('README.md').read(),
      url='http://github.com/rynecarbone/power_ranker',
      author='Ryne Carbone',
      author_email='ryne.carbone@gmail.com',
      license='MIT',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
      ],
      packages=find_packages(),
      include_package_data = True,
      install_requires=[
        'bs4',
        'configparser',
        'lxml',
        'matplotlib',
        'numpy',
        'pandas',
        'requests',
        'scipy',
        'plotnine'
      ],
      python_requires='>=3',
      entry_points={
        'console_scripts': [
          'power_ranker = scripts.command_line:main',
          'copy_config = scripts.command_line:copy_config'
        ]
      },
      zip_safe=False)
