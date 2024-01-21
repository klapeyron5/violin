from copy import deepcopy
from .static_declaration import DecsChecker, get_DecsFromTupleToDec


class TransformInit:
    _DEC_TEMPLATE_DINIT = 'DINIT'
    _DECS_INIT = (_DEC_TEMPLATE_DINIT,)  # TODO intersection with other _DECS
    _DECS_INIT_STARTSWITH = tuple(x+'_' for x in _DECS_INIT)
    def __init__(self, **cnfg):
        self._init(**cnfg)
    def _init(self, **cnfg):
        raise NotImplementedError


class TransformCall:
    _DEC_TEMPLATE_DCALL_IMM = 'DCALL_IMM'
    _DEC_TEMPLATE_DCALL_MUT = 'DCALL_MUT'
    _DEC_TEMPLATE_DCALL_OUT = 'DCALL_OUT'
    _DECS_CALL = (_DEC_TEMPLATE_DCALL_IMM, _DEC_TEMPLATE_DCALL_MUT, _DEC_TEMPLATE_DCALL_OUT)  # TODO intersection with other _DECS
    _DECS_CALL_STARTSWITH = tuple(x+'_' for x in _DECS_CALL)
    def __call__(self, **data):
        return self._call(**data)
    def _call(self, **data):
        raise NotImplementedError


class InitPipe(TransformInit):
    def __init__(self, **cnfg):
        # init_DecsFromTupleToDec(self, TransformInit._DECS_INIT_STARTSWITH)
        cnfg_keys_checker = DecsChecker(decs=getattr(self, 'decs_'+self._DEC_TEMPLATE_DINIT), check_values=True, use_default_values=True)
        cnfg, cnfg_external = cnfg_keys_checker(**cnfg)
        assert set(cnfg_external.keys()) == set(), f"""All init keys should be defined as {self._DEC_TEMPLATE_DINIT}_.
These keys are not defined: {cnfg_external.keys()}."""
        super().__init__(**cnfg)


class _CallPipe(TransformCall):
    def __init__(self, keys_call_imm, keys_call_mut, keys_call_out):
        call_imm_and_call_mut = set(keys_call_imm) & set(keys_call_mut)
        assert call_imm_and_call_mut == set(), f"Error: intersection between keys_call_imm and keys_call_mut: {call_imm_and_call_mut}."
        call_imm_and_out = set(keys_call_out) & set(keys_call_imm)
        assert call_imm_and_out == set(), f"Error: intersection between keys_call_imm and keys_call_out: {call_imm_and_out}."

        self.__call_keys_checker = DecsChecker(decs=set(keys_call_imm) | set(keys_call_mut), check_values=False, use_default_values=True)
        self.__call_mut_keys_checker = DecsChecker(decs=keys_call_mut, check_values=True, use_default_values=False)
        self.__call_out_keys_checker = DecsChecker(decs=keys_call_out, check_values=True, use_default_values=True)
        super().__init__()

    def __call__(self, **data):
        data, data_call_imm, data_call_mut = self._before(data)
        for k in data_call_imm:
            data_call_mut[k] = deepcopy(data_call_imm[k])
        data_out = super().__call__(**data_call_mut)
        data = self._after(data, data_call_imm, data_out)
        return data

    def _before(self, data):
        for x in data.keys():
            if not isinstance(x, str):
                print(x)
                assert False

        data_call, data_ext = self.__call_keys_checker(**data)
        intersection_call_ext = set(data_call.keys()) & set(data_ext.keys())
        assert intersection_call_ext == set(), "There is intersection between external and call data: {}".format(intersection_call_ext)
        assert set(data.keys()) - (set(data_call.keys()) | set(data_ext.keys())) == set()
        data = data_ext

        data_call_mut, data_call_imm = self.__call_mut_keys_checker(**data_call)
        assert set(data_call_mut.keys()) & set(data_call_imm.keys()) == set()  # TODO delete
        assert set(data_call_mut.keys()) | set(data_call_imm.keys()) == set(data_call.keys())  # TODO delete
        return data, data_call_imm, data_call_mut

    def _after(self, data, data_call_imm, data_call_out):
        data_call_out, _data = self.__call_out_keys_checker(**data_call_out)
        assert len(_data.keys()) == 0, f"Check returned keys for {self}; These keys are not declared as DCALL_OUT: {_data.keys()}"
        assert set(data_call_out.keys()) & set(data_call_imm.keys()) == set()  # TODO delete
        common_keys = set(data_call_out.keys()) & set(data.keys())
        assert common_keys == set(), f'Common keys: {common_keys}'
        data.update(data_call_imm)
        data.update(data_call_out)
        assert all([isinstance(x, str) for x in data.keys()])
        return data


class CallPipe(_CallPipe):
    def __init__(self):
        # init_DecsFromTupleToDec(self, TransformCall._DECS_CALL_STARTSWITH)
        super().__init__(
            keys_call_imm=getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_IMM),
            keys_call_mut=getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_MUT),
            keys_call_out=getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_OUT),
        )


class Transform(
        InitPipe, CallPipe,
        # meta cas I need to use decs as str dict keys when initing or calling instance of transform:
        metaclass=get_DecsFromTupleToDec(TransformInit._DECS_INIT_STARTSWITH+TransformCall._DECS_CALL_STARTSWITH),
    ):
    """
    Decs (declarations):

    DINIT_example = (value_checker: callable(x)->None, default_value: callable()->x)  # fully defined dec

    DCALL_IMM_example1 = (value_checker, None)  # no default value
    DCALL_MUT_example2 = (None, default_value)  # no value_checker

    DCALL_OUT_example1 = ...  # error: it makes no sense to return immutable (IMM) variable
    DCALL_OUT_example2 = ...  # allowed
    DCALL_OUT_some_new_key = ...  # allowed
    
    when initing, DINIT_example becomes 'example' string for cnfg for __init__(self, **cnfg)
    similarly with the __call__(self, **data)

    Does not check DCALL_IMM keys !

    to implement:
    _init(self, **cnfg)
    _call(self, **data)
    """
    def __init__(self, **cnfg):
        InitPipe.__init__(self, **cnfg)
        CallPipe.__init__(self,)
