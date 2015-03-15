def returner(x):
    """
    Create a function that takes any arguments and always
    returns x.
    """
    def func(*args, **kwargs):
        return x
    return func


def impartial(f, *args, **kwargs):
    """
    Acts just like Python's functools.partial, except that any arguments
    to the returned function are ignored (making it 'impartial', get it?)
    """
    def func(*_a, **_k):
        return f(*args, **kwargs)
    return func
