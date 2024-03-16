from .transform import InitPipe, CallPipe, Transform


class TransformPipeline(Transform):
    """
    Runs sequence of Transforms.
    """
    
    @classmethod
    def check_transforminstances(cls, transforms):  # TODO check and map all in-out dicts into CALL-OUT decs
        assert isinstance(transforms, list)
        assert all([isinstance(x, Transform) for x in transforms])
    
    DINIT_transforminstances = (check_transforminstances, lambda: list())

    def get_dataflow(self):
        DCALL_IMM = set()
        DCALL_MUT = set()
        DCALL_OUT = set()
        for t in self._transforms:
            DCALL_IMM = DCALL_IMM | t.decs_DCALL_IMM_
            DCALL_MUT = DCALL_MUT | t.decs_DCALL_MUT_
            DCALL_OUT = DCALL_OUT | t.decs_DCALL_OUT_
        DCALL_IMM = DCALL_IMM - DCALL_MUT
        DCALL_IMM = DCALL_IMM - DCALL_OUT
        return DCALL_IMM, DCALL_MUT, DCALL_OUT

    def __init__(self, **cnfg):
        InitPipe.__init__(self, **cnfg)
        
        for tmplt, decs in zip([
            self._DEC_TEMPLATE_DCALL_IMM_, self._DEC_TEMPLATE_DCALL_MUT_, self._DEC_TEMPLATE_DCALL_OUT_],
            self.get_dataflow()):
            setattr(self, 'decs_'+tmplt, decs)
            for dec in decs:
                setattr(self, tmplt+str(dec), dec)
        CallPipe.__init__(self,)
    
    def _init(self, **cnfg):
        self._transforms = cnfg[self.DINIT_transforminstances]

    def _call(self, **data):
        for op in self._transforms:
            data = op(**data)
        for imm_key in self.decs_DCALL_IMM_:
            del data[imm_key]
        return data
