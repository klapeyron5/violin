class ViolinException(Exception):
    pass

class DecException(ViolinException):
    pass

class DecCheckException(DecException):
    pass

class DecDefaultException(DecException):
    def __init__(self, parent=None, dec=None, e=None):
        self.parent = parent
        self.dec = dec
        self.e = e
