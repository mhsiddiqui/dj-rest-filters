import codecs
import os
import re

from setuptools import find_packages, setup


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='dj-rest-filters',
    version=find_version("djfilters", "__init__.py"),
    url="https://github.com/mhsiddiqui/dj-rest-filters",
    description='Django Rest Filter',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Muhammad Hassan Siddiqui',
    author_email='mhassan.eeng@gmail.com',
    license='MIT',
    keywords='django filters filter-backend dj-rest-filters'.split(),
    platforms=['any'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3',
    extras_require={
        'django': ['Django>1.10'],
        'six': ['six>1.1'],
        'djangorestframework': ['djangorestframework>3.3']
    }
)
