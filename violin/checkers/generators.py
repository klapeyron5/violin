from .. import Transform


def nullable(checker):
    def body(x):
        if x is not None:
            checker(x)
    return body

def unite(*args):
    def body(x):
        for a in args:
            a(x)
    return body
