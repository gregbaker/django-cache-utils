from hashlib import sha256
from django.utils.encoding  import smart_str

CONTROL_CHARACTERS = set([chr(i) for i in range(0,33)])
CONTROL_CHARACTERS.add(chr(127))

def sanitize_memcached_key(key, max_length=100):
    """ Removes control characters and ensures that key will
        not hit the memcached key length limit by replacing
        the key tail with md5 hash if key is too long.
    """
    key = ''.join([c for c in key if c not in CONTROL_CHARACTERS])
    key = key.encode('utf8')
    key = key[:max_length-65] + b'-' + sha256(key).hexdigest().encode('utf8')
    return key

def _args_to_unicode(args, kwargs):
    key = ""
    if args:
        key += smart_str(args)
    if kwargs:
        key += smart_str(kwargs)
    return key


def _func_type(func):
    """ returns if callable is a function, method or a classmethod """
    try:
        argnames = func.__code__.co_varnames[:func.__code__.co_argcount] # Python 3
    except AttributeError:
        argnames = func.func_code.co_varnames[:func.func_code.co_argcount] # Python 2
    if len(argnames) > 0:
        if argnames[0] == 'self':
            return 'method'
        if argnames[0] == 'cls':
            return 'classmethod'
    return 'function'


def _func_info(func, args):
    ''' introspect function's or method's full name.
    Returns a tuple (name, normalized_args,) with
    'cls' and 'self' removed from normalized_args '''

    func_type = _func_type(func)
    try:
        lineno = ":%s" % func.__code__.co_firstlineno # Python 3
    except AttributeError:
        lineno = ":%s" % func.func_code.co_firstlineno # Python 2

    if func_type == 'function':
        name = ".".join([func.__module__, func.__name__]) + lineno
        return name, args

    class_name = args[0].__class__.__name__
    if func_type == 'classmethod':
        class_name = args[0].__name__

    name = ".".join([func.__module__, class_name, func.__name__]) + lineno
    return name, args[1:]


def _cache_key(func_name, func_type, args, kwargs):
    """ Construct readable cache key """
    if func_type == 'function':
        args_string = _args_to_unicode(args, kwargs)
    else:
        args_string = _args_to_unicode(args[1:], kwargs)
    return '[cached]%s(%s)' % (func_name, args_string,)
