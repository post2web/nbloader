# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


setup(
    name='nbloader',
    version='1.0.6',
    description='Reuse code from Jupyter Notebooks',
    url='https://github.com/post2web/nbloader',
    download_url = 'https://github.com/post2web/nbloader/archive/1.0.6.tar.gz',
    author='Ivelin Angelov',
    author_email='post2web@gmail.com',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords=['jupyter notebook', 'jupyter', 'notebook', 'reuse notebook'],

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=find_packages(exclude=['contrib', 'docs', 'tests', 'tutorial']),
    packages=['nbloader'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["nbloader"],

    install_requires=[
        'IPython', 'nbformat', #'ipywidgets'
    ],
)
