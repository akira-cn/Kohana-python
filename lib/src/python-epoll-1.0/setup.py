#!/usr/bin/env python

# Written by Ross Cohen

from distutils.core import setup, Extension

setup(
    name = "python-epoll",
    version = "1.0",
    author = "Ross Cohen",
    author_email = "rcohen@snurgle.org",
    license = "BSD",
    url = "http://sourceforge.net/projects/pyepoll/",
    download_url = "http://sourceforge.net/project/showfiles.php?group_id=163263",
    classifiers = ['Development Status :: 5 - Production/Stable'],

    ext_modules=[Extension("epoll", ["epollmodule.c"])],
    data_files= [('share/doc/python-epoll', ['README.txt'])],

    description = "python-epoll is a drop-in replacement for the python standard library select module using the more efficient epoll system call as the backend instead of poll.",
    long_description = "python-epoll is a drop-in replacement for the python standard library select module using the more efficient epoll system call as the backend instead of poll.",
)
