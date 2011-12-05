/* epoll - Module containing unix epoll_wait(2) call.*/
/*
Copyright (c) 2005, Ross Cohen

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * Neither the name of the Ross Cohen nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include "Python.h"

#ifndef FD_SETSIZE
#define FD_SETSIZE 512
#endif

#include <sys/epoll.h>

#ifndef DONT_HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif

#define SOCKET int

static PyObject *SelectError;

/*
 * epoll() support
 */

typedef struct {
        PyObject_HEAD
        PyObject *dict;
        SOCKET epfd;
        struct epoll_event ufds[FD_SETSIZE];
} pollObject;

static PyTypeObject poll_Type;

PyDoc_STRVAR(poll_register_doc,
"register(fd [, eventmask] ) -> None\n\n\
Register a file descriptor with the polling object.\n\
fd -- either an integer, or an object with a fileno() method returning an\n\
      int.\n\
events -- an optional bitmask describing the type of events to check for");

static PyObject *
poll_register(pollObject *self, PyObject *args)
{
        PyObject *o, *key, *value;
        struct epoll_event event;
        int fd, events = EPOLLIN | EPOLLPRI | EPOLLOUT;
        int err, epoll_op = EPOLL_CTL_ADD;

        if (!PyArg_ParseTuple(args, "O|i:register", &o, &events)) {
                return NULL;
        }

        fd = PyObject_AsFileDescriptor(o);
        if (fd == -1) return NULL;

        /* Add entry to the internal dictionary: the key is the
           file descriptor, and the value is the event mask. */
        key = PyInt_FromLong(fd);
        if (key == NULL)
                return NULL;

        /* Test if it's already in the set */
        value = PyDict_GetItem(self->dict, key);
        if (value != NULL) {
                epoll_op = EPOLL_CTL_MOD;
                //Py_DECREF(value);
        }

        err = PyDict_SetItem(self->dict, key, o);
        Py_DECREF(key);
        if (err < 0)
                return NULL;

        event.events = events;
        //event.data.ptr = (void *)o;
        event.data.fd = fd;
        if (epoll_ctl(self->epfd, epoll_op, fd, &event) == -1) {
            PyErr_SetFromErrno(SelectError);
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
}

PyDoc_STRVAR(poll_unregister_doc,
"unregister(fd) -> None\n\n\
Remove a file descriptor being tracked by the polling object.");

static PyObject *
poll_unregister(pollObject *self, PyObject *args)
{
        PyObject *o, *key;
        int fd;

        if (!PyArg_ParseTuple(args, "O:unregister", &o)) {
                return NULL;
        }

        fd = PyObject_AsFileDescriptor( o );
        if (fd == -1)
                return NULL;

        /* Check whether the fd is already in the array */
        key = PyInt_FromLong(fd);
        if (key == NULL)
                return NULL;

        if (PyDict_DelItem(self->dict, key) == -1) {
                Py_DECREF(key);
                /* This will simply raise the KeyError set by PyDict_DelItem
                   if the file descriptor isn't registered. */
                return NULL;
        }

        Py_DECREF(key);

        if (-1 == epoll_ctl(self->epfd, EPOLL_CTL_DEL, fd, NULL)) {
                /* If the socket is already closed this fails */
                if (errno != EBADF) {
                        PyErr_SetFromErrno(SelectError);
                        return NULL;
                }
        }

        Py_INCREF(Py_None);
        return Py_None;
}

PyDoc_STRVAR(poll_poll_doc,
"poll( [timeout] ) -> list of (fd, event) 2-tuples\n\n\
Polls the set of registered file descriptors, returning a list containing \n\
any descriptors that have events or errors to report.");

static PyObject *
poll_poll(pollObject *self, PyObject *args)
{
        PyObject *result_list = NULL, *tout = NULL;
        int timeout = 0, poll_result, i;
        PyObject *value = NULL, *num = NULL;

        if (!PyArg_ParseTuple(args, "|O:poll", &tout)) {
                return NULL;
        }

        /* Check values for timeout */
        if (tout == NULL || tout == Py_None)
                timeout = -1;
        else if (!PyNumber_Check(tout)) {
                PyErr_SetString(PyExc_TypeError,
                                "timeout must be an integer or None");
                return NULL;
        }
        else {
                tout = PyNumber_Int(tout);
                if (!tout)
                        return NULL;
                timeout = PyInt_AsLong(tout);
                Py_DECREF(tout);
        }

        /* call epoll() */
        Py_BEGIN_ALLOW_THREADS;
        poll_result = epoll_wait(self->epfd, self->ufds, FD_SETSIZE, timeout);
        Py_END_ALLOW_THREADS;

        if (poll_result < 0) {
                PyErr_SetFromErrno(SelectError);
                return NULL;
        }

        /* build the result list */

        result_list = PyList_New(poll_result);
        if (!result_list)
                return NULL;
        else {
                for (i = 0; i < poll_result; i++) {
                        /* if we hit a NULL return, set value to NULL
                           and break out of loop; code at end will
                           clean up result_list */
                        value = PyTuple_New(2);
                        if (value == NULL)
                                goto error;
                        //num = (PyObject *)(self->ufds[i].data.ptr);
                        num = PyInt_FromLong(self->ufds[i].data.fd);
                        if (num == NULL) {
                                Py_DECREF(value);
                                goto error;
                        }
                        //Py_INCREF(num);
                        PyTuple_SET_ITEM(value, 0, num);

                        num = PyInt_FromLong(self->ufds[i].events);
                        if (num == NULL) {
                                Py_DECREF(value);
                                goto error;
                        }
                        PyTuple_SET_ITEM(value, 1, num);
                        if ((PyList_SetItem(result_list, i, value)) == -1) {
                                Py_DECREF(value);
                                goto error;
                        }
                }
        }
        return result_list;

  error:
        Py_DECREF(result_list);
        return NULL;
}

static PyMethodDef poll_methods[] = {
        {"register",    (PyCFunction)poll_register,
         METH_VARARGS,  poll_register_doc},
        {"unregister",  (PyCFunction)poll_unregister,
         METH_VARARGS,  poll_unregister_doc},
        {"poll",        (PyCFunction)poll_poll,
         METH_VARARGS,  poll_poll_doc},
        {NULL,          NULL}           /* sentinel */
};

static pollObject *
newPollObject(void)
{
        pollObject *self;
        self = PyObject_New(pollObject, &poll_Type);
        if (self == NULL)
                return NULL;
        self->dict = PyDict_New();
        if (self->dict == NULL) {
                Py_DECREF(self);
                return NULL;
        }
        self->epfd = epoll_create(FD_SETSIZE);
        if (self->epfd == -1) {
                Py_DECREF(self);
                PyErr_SetFromErrno(SelectError);
                return NULL;
        }
        return self;
}

static void
poll_dealloc(pollObject *self)
{
        Py_XDECREF(self->dict);
        close(self->epfd);
        PyObject_Del(self);
}

static PyObject *
poll_getattr(pollObject *self, char *name)
{
        return Py_FindMethod(poll_methods, (PyObject *)self, name);
}

static PyTypeObject poll_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "epoll.poll",           /*tp_name*/
        sizeof(pollObject),     /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        (destructor)poll_dealloc, /*tp_dealloc*/
        0,                      /*tp_print*/
        (getattrfunc)poll_getattr, /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
};

PyDoc_STRVAR(poll_doc,
"Returns a polling object, which supports registering and\n\
unregistering file descriptors, and then polling them for I/O events.");

static PyObject *
epoll_poll(PyObject *self, PyObject *args)
{
        pollObject *rv;

        if (!PyArg_ParseTuple(args, ":poll"))
                return NULL;
        rv = newPollObject();
        if ( rv == NULL )
                return NULL;
        return (PyObject *)rv;
}

static PyMethodDef epoll_methods[] = {
    {"poll",    epoll_poll,   METH_VARARGS, poll_doc},
    {0,         0},                          /* sentinel */
};

PyDoc_STRVAR(module_doc,
"This module supports asynchronous I/O on multiple file descriptors.\n");

PyMODINIT_FUNC
initepoll(void)
{
        PyObject *m;
        m = Py_InitModule3("epoll", epoll_methods, module_doc);

        SelectError = PyErr_NewException("epoll.error", NULL, NULL);
        Py_INCREF(SelectError);
        PyModule_AddObject(m, "error", SelectError);
        poll_Type.ob_type = &PyType_Type;
        PyModule_AddIntConstant(m, "POLLNVAL", 0); /* no equivalent */
        PyModule_AddIntConstant(m, "POLLIN",  EPOLLIN);
        PyModule_AddIntConstant(m, "POLLPRI", EPOLLPRI);
        PyModule_AddIntConstant(m, "POLLOUT", EPOLLOUT);
        PyModule_AddIntConstant(m, "POLLERR", EPOLLERR);
        PyModule_AddIntConstant(m, "POLLHUP", EPOLLHUP);

#ifdef EPOLLRDNORM
        PyModule_AddIntConstant(m, "POLLRDNORM", EPOLLRDNORM);
#endif
#ifdef EPOLLRDBAND
        PyModule_AddIntConstant(m, "POLLRDBAND", EPOLLRDBAND);
#endif
#ifdef EPOLLWRNORM
        PyModule_AddIntConstant(m, "POLLWRNORM", EPOLLWRNORM);
#endif
#ifdef EPOLLWRBAND
        PyModule_AddIntConstant(m, "POLLWRBAND", EPOLLWRBAND);
#endif
#ifdef EPOLLMSG
        PyModule_AddIntConstant(m, "POLLMSG", EPOLLMSG);
#endif
}
