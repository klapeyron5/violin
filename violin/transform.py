from copy import deepcopy
import inspect, re
from violin.static_declaration import dec_generator, Dec, DecsChecker
from violin.exception import ViolinException, DecDefaultException, DecCheckException, DecsFlowException


class TransformInit:
    _DEC_TEMPLATE_DINIT = 'DINIT'
    _DECS_INIT = (_DEC_TEMPLATE_DINIT,)  # TODO intersection with other _DECS
    _DECS_INIT_STARTSWITH = tuple(x+'_' for x in _DECS_INIT)
    def __init__(self, **cnfg):
        self._init(**cnfg)
    def _init(self, **cnfg):
        # raise ViolinException
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
    
    @staticmethod
    def _check_call_decs_intersection(keys_call_imm, keys_call_mut, keys_call_out):
        args = [keys_call_imm, keys_call_mut, keys_call_out]
        assert all([isinstance(s, set) for s in args])
        assert all([all([isinstance(x, str) for x in s]) for s in args])

        call_imm_and_call_mut = set(keys_call_imm) & set(keys_call_mut)
        assert call_imm_and_call_mut == set(), f"Error: intersection between keys_call_imm and keys_call_mut: {call_imm_and_call_mut}."
        call_imm_and_out = set(keys_call_out) & set(keys_call_imm)
        assert call_imm_and_out == set(), f"Error: intersection between keys_call_imm and keys_call_out: {call_imm_and_out}."


class InitPipe(TransformInit):
    def __init__(self, **cnfg):
        # init_DecsFromTupleToDec(self, TransformInit._DECS_INIT_STARTSWITH)
        cnfg_keys_checker = DecsChecker(decs=getattr(self, 'decs_'+self._DEC_TEMPLATE_DINIT), check_values=True, use_default_values=True, deepcopy_checked_values=False)
        cnfg, cnfg_external = cnfg_keys_checker(**cnfg)
        assert set(cnfg_external.keys()) == set(), f"""All init keys should be defined as {self._DEC_TEMPLATE_DINIT}_.
These keys are not defined: {cnfg_external.keys()}."""
        super().__init__(**cnfg)


class _CallPipe(TransformCall):
    def __init__(self, keys_call_imm, keys_call_mut, keys_call_out):
        self._check_call_decs_intersection(keys_call_imm, keys_call_mut, keys_call_out)

        self.__call_keys_checker = DecsChecker(decs=set(keys_call_imm) | set(keys_call_mut), check_values=False, use_default_values=True)
        self.__call_mut_keys_checker = DecsChecker(decs=keys_call_mut, check_values=True, use_default_values=False, deepcopy_checked_values=True)
        self.__call_out_keys_checker = DecsChecker(decs=keys_call_out, check_values=True, use_default_values=True, deepcopy_checked_values=True)
        super().__init__()

    def __call__(self, **data):
        try:
            data, data_call_imm, data_call_mut = self._before(data)
        except DecDefaultException as e:
            raise DecDefaultException(parent=self, dec=e.dec, e=e.e)
        except DecCheckException as e:
            raise DecCheckException(parent=self, dec=e.dec, e=e.e)
        
        try:
            for k in data_call_imm:
                data_call_mut[k] = deepcopy(data_call_imm[k])
        except ViolinException as e:
            pass # cant deepcopy an object for DCALL_IMM

        data_out = super().__call__(**data_call_mut)

        try:
            data = self._after(data, data_call_imm, data_out)
        except DecDefaultException as e:
            raise DecDefaultException(parent=self, dec=e.dec, e=e.e)
        except DecCheckException as e:
            raise DecCheckException(parent=self, dec=e.dec, e=e.e)
        return data

    def _before(self, data):
        for x in data.keys():
            if not isinstance(x, str):
                print(x)
                assert False

        try:
            data_call, data_ext = self.__call_keys_checker(**data)
        except DecsFlowException as e:
            raise DecsFlowException(not_matched_data_keys=e.not_matched_data_keys, data_keys=e.data_keys, decs=e.decs, flow_stage='before call; input keys vs call keys', transform=self)
        data = data_ext

        try:
            data_call_mut, data_call_imm = self.__call_mut_keys_checker(**data_call)
        except DecsFlowException as e:
            raise DecsFlowException(not_matched_data_keys=e.not_matched_data_keys, data_keys=e.data_keys, decs=e.decs, flow_stage='before call; imm vs mut call keys', transform=self)
        return data, data_call_imm, data_call_mut

    def _after(self, data, data_call_imm, data_call_out):
        try:
            data_call_out, _data = self.__call_out_keys_checker(**data_call_out)
        except DecsFlowException as e:
            raise DecsFlowException(not_matched_data_keys=e.not_matched_data_keys, data_keys=e.data_keys, decs=e.decs, flow_stage='after call; out call keys', transform=self)
        if len(_data) != 0:
            raise DecsFlowException(not_matched_data_keys=_data, data_keys=data_call_out, decs=self.__call_out_keys_checker.decs, flow_stage='after call; out call keys', transform=self)
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


def get_DecsFromTupleToDec():
    templates_startswith = TransformInit._DECS_INIT_STARTSWITH+TransformCall._DECS_CALL_STARTSWITH
    assert isinstance(templates_startswith, tuple), templates_startswith
    assert all([re.match(Dec.DecKey.RE_TEMPLATE_STARTSWITH, x) is not None for x in templates_startswith]), templates_startswith

    def preproc_classmethod(func, cls):
        c0 = isinstance(func, classmethod)
        if c0 or isinstance(func, staticmethod):
            # decide that vv is @classmethod of this cls and vv should be transformed
            assert not hasattr(func, '__self__')
            func_namespace = (func.__module__+'.'+func.__qualname__).split('.')
            func_name = func_namespace[-1]
            func_clsnamespace = func_namespace[:-1]
            cls_namespace = (cls.__module__+'.'+cls.__qualname__).split('.')
            assert func_clsnamespace == cls_namespace,\
                f"U can use not bounded classmethod only from current class \
{'.'.join(cls_namespace)}, but u r using from {'.'.join(func_clsnamespace)}"
            func = getattr(cls, func_name)
            if c0:
                assert func.__self__ is cls
        return func

    class DecsFromTupleToDec(type):
        TEMPLATES_STARTSWITH = templates_startswith

        def __init__(cls, name, bases, attrs):
            for template_startswith in cls.TEMPLATES_STARTSWITH:
                decs = set()
                # for attr_name in get_decs_attrnames_in_order(cls, template_startswith):
                for attr_info in inspect.getmembers(cls):
                    attr_name = attr_info[0]
                    if attr_name.startswith(template_startswith):
                        v = getattr(cls, attr_name)
                        if isinstance(v, Dec):
                            assert attr_name[len(template_startswith):] == v, f"{attr_name} != {v} for cls {cls}"
                            dec = v
                        else:
                            assert isinstance(v, tuple), f"{attr_name}: {v}"
                            assert len(v) == 2, f"{attr_name}: {v}"
                            v = tuple([preproc_classmethod(x, cls) for x in v])
                            dec = dec_generator(attr_name, template_startswith, v)
                        setattr(cls, attr_name, dec)
                        decs.add(dec)
                setattr(cls, 'decs_'+template_startswith[:-1], decs)
            TransformCall._check_call_decs_intersection(*[getattr(cls, 'decs_'+d) for d in TransformCall._DECS_CALL])

    return DecsFromTupleToDec


class Transform(
        InitPipe, CallPipe,
        # meta cas I need to use decs as str dict keys when initing or calling instance of transform:
        metaclass=get_DecsFromTupleToDec(),
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

    DINIT keys checked without copying
    DCALL_IMM keys does not checked 
    DCALL_MUT keys are checked
    DCALL_OUT keys are checked

    to implement:
    _init(self, **cnfg)
    _call(self, **data)
    """
    def __init__(self, **cnfg):
        # try:
        InitPipe.__init__(self, **cnfg)
        CallPipe.__init__(self,)
        # except ViolinException as e:
        #     raise ViolinException from None
