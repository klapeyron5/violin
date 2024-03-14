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
    def __init__(self, not_matched_data_keys, data_keys, decs, flow_stage=None, transform=None):
        self.not_matched_data_keys, self.data_keys, self.decs, self.flow_stage, self.transform \
            = not_matched_data_keys, data_keys, decs, flow_stage, transform
    def __str__(self):
        return f"""Declarations flow error at transform {self.transform} at stage {self.flow_stage}.
Declarations {str(self.decs)} didn't match with data_keys: {str(self.data_keys)}.
Some problematic keys: {str(self.not_matched_data_keys)}."""
