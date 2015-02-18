import scanomatic.io.logger as logger

import time
import datetime
import multiprocessing
from inspect import ismethod
from threading import Thread


class UnknownLock(KeyError):
    pass

#
#   CLASS PROPERTY
#


class _ClassPropertyDescriptor(object):

    def __init__(self, get_function, set_function=None):
        self._get_function = get_function
        self._set_function = set_function

    def __get__(self, obj, cls=None):
        if cls is None:
            cls = type(obj)
        return self._get_function.__get__(obj, cls)()

    def __set__(self, obj, value):
        if not self._set_function:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self._set_function.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self._set_function = func
        return self


def class_property(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return _ClassPropertyDescriptor(func)


def _get_id_tuple(f, args, kwargs, mark=object()):

    l = [id(f)]
    for arg in args:
        l.append(id(arg))
    l.append(id(mark))
    for k, v in kwargs:
        l.append(k)
        l.append(id(v))
    return tuple(l)

#
#   MEMOIZATION
#

_MEMOIZED = {}


def memoize(f):

    def memoized(*args, **kwargs):
        key = _get_id_tuple(f, args, kwargs)
        if key not in _MEMOIZED:
            _MEMOIZED[key] = f(*args, **kwargs)
        return _MEMOIZED[key]
    return memoized


#
#   TIMING
#

_TIME_LOGGER = logger.Logger("Time It")


def timeit(f):

    def timer(*args, **kwargs):

        t = time.time()
        _TIME_LOGGER.info("Calling {0}".format(f))
        ret = f(*args, **kwargs)
        _TIME_LOGGER.info("Call to {0} lasted {1}".format(f, str(datetime.timedelta(seconds=time.time() - t))))
        return ret

    return timer


#
#   PATH LOCKING
#

_PATH_LOCK = dict()


def path_lock(f):

    def _acquire(path):
        global _PATH_LOCK
        try:
            while not _PATH_LOCK[path].acquire(False):
                time.sleep(0.05)
        except KeyError:
            raise UnknownLock("Path '{0}' not registered by {1}".format(path, register_path_lock))

    def locking_wrapper_method(self_cls, path, *args, **kwargs):
        global _PATH_LOCK
        _acquire(path)
        ret = f(self_cls, path, *args, **kwargs)
        _PATH_LOCK[path].release()
        return ret

    def locking_wrapper_function(path, *args, **kwargs):
        global _PATH_LOCK
        _acquire(path)
        ret = f(path, *args, **kwargs)
        _PATH_LOCK[path].release()
        return ret

    if ismethod(f):
        return locking_wrapper_method
    else:
        return locking_wrapper_function


def register_path_lock(path):
    global _PATH_LOCK
    _PATH_LOCK[path] = multiprocessing.Lock()


#
#   TYPE LOCKING
#

_TYPE_LOCK = {}


def register_type_lock(object_instance):
    global _TYPE_LOCK
    _TYPE_LOCK[type(object_instance)] = multiprocessing.Lock()


def type_lock(f):

    def _acquire(object_type):
        global _TYPE_LOCK
        try:
            while not _TYPE_LOCK[object_type].acquire(False):
                time.sleep(0.05)
        except KeyError:
            raise UnknownLock("{0} never registered by (1)".format(object_type, register_type_lock))

    def locking_wrapper(self, *args, **kwargs):
        global _TYPE_LOCK
        object_type = type(self)
        _acquire(object_type)
        result = f(self, *args, **kwargs)
        _TYPE_LOCK[object_type].release()
        return result

    return locking_wrapper

#
#   THREADING
#


def threaded(f):

    def _threader(*args, **kwargs):

        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()

    return _threader