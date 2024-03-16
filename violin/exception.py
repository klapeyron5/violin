class ViolinException(Exception):
    pass

class DecException(ViolinException):
    def __init__(self, parent=None, dec=None, e=None):
        self.parent = parent
        self.dec = dec
        self.e = e

class DecCheckException(DecException):
    pass

class DecDefaultException(DecException):
    pass

class DecsFlowException(ViolinException):
    def __init__(self, not_matched_keys, list_of_name__keys_set, flow_stage=None, transform=None):
        self.not_matched_keys, self.list_of_name__keys_set, self.flow_stage, self.transform \
            = not_matched_keys, list_of_name__keys_set, flow_stage, transform
    def __str__(self):
        return f"""Declarations flow error at transform {self.transform} at the stage "{self.flow_stage}".
List of (name, keys_set): {str(self.list_of_name__keys_set)}.
Some problematic keys: {str(self.not_matched_keys)}."""
