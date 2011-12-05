== Introduction ==

python-epoll is a drop-in replacement for the python standard library select
module using the more efficient epoll system call as the backend instead
of poll.

epoll scales to thousands of open sockets without the large CPU overhead
imposed by poll under the same circumstances. See:
http://lse.sourceforge.net/epoll/index.html

This software is released under the new BSD license.


== Status ==

This software is stable and has been used in a heavy production environment
for a year with no issues.

== Usage ==

If you are using the select module directly in your code, then the following
should suffice to convert to using python-epoll:

import epoll as select

If you are using a module which uses select, you will have to do a little more
work, but not a lot. Here's an example using asyncore:

import select
import epoll

for attr in ['poll', 'error', 'POLLIN', 'POLLPRI', 'POLLOUT', 'POLLERR', 'POLLHUP', 'POLLNVAL']:
    setattr(select, attr, getattr(epoll, attr))
 
import asyncore 


== What isn't python-epoll ==

python-epoll does not implement an equivalent of the select.select() method.
It only implements the select.poll() interface. Any code which depends on the
former will not be able to make use of this software.


== Contact ==

Submit issues and discuss at:
http://sourceforge.net/projects/pyepoll/

