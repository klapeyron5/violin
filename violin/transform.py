from copy import deepcopy
import inspect, re
from violin.static_declaration import dec_generator, Dec, DecsChecker
from violin.exception import ViolinException, DecDefaultException, DecCheckException, DecsFlowException


class TransformInit:
    _DEC_TEMPLATE_DINIT_ = 'DINIT_'
    _DECS_TEMPLATES_DINIT_ = (_DEC_TEMPLATE_DINIT_,)  # TODO intersection with other _DECS
    def __init__(self, **cnfg):
        self._init(**cnfg)
    def _init(self, **cnfg):
        # raise ViolinException
        raise ViolinException('Not implemented _init')


class TransformCall:
    _DEC_TEMPLATE_DCALL_IMM_ = 'DCALL_IMM_'
    _DEC_TEMPLATE_DCALL_MUT_ = 'DCALL_MUT_'
    _DEC_TEMPLATE_DCALL_OUT_ = 'DCALL_OUT_'
    _DECS_TEMPLATES_DCALL_ = (_DEC_TEMPLATE_DCALL_IMM_, _DEC_TEMPLATE_DCALL_MUT_, _DEC_TEMPLATE_DCALL_OUT_)  # TODO intersection with other _DECS
    def __call__(self, **data):
        return self._call(**data)
    def _call(self, **data):
        raise ViolinException('Not implemented _call')
    
    @staticmethod
    def _check_call_decs(keys_call_imm, keys_call_mut, keys_call_out):
        args = [keys_call_imm, keys_call_mut, keys_call_out]
        assert all([isinstance(s, set) for s in args])
        assert all([all([isinstance(x, str) for x in s]) for s in args])

        call_imm_and_mut = set(keys_call_imm) & set(keys_call_mut)
        if call_imm_and_mut != set():
            raise DecsFlowException(
                not_matched_keys=call_imm_and_mut,
                list_of_name__keys_set=[
                    ('keys DCALL_IMM', keys_call_imm),
                    ('keys DCALL_MUT', keys_call_mut),
                ],
                flow_stage=None,
                transform=None,
            )
        call_imm_and_out = set(keys_call_out) & set(keys_call_imm)
        if call_imm_and_out != set():
            raise DecsFlowException(
                not_matched_keys=call_imm_and_out,
                list_of_name__keys_set=[
                    ('keys DCALL_IMM', keys_call_imm),
                    ('keys DCALL_OUT', keys_call_out),
                ],
                flow_stage=None,
                transform=None,
            )


class InitPipe(TransformInit):
    def __init__(self, **cnfg):
        cnfg_keys_checker = DecsChecker(decs=getattr(self, 'decs_'+self._DEC_TEMPLATE_DINIT_), check_values=True, use_default_values=True, deepcopy_checked_values=False)
        cnfg, cnfg_external = cnfg_keys_checker(**cnfg)
        assert set(cnfg_external.keys()) == set(), f"""All init keys should be defined as {self._DEC_TEMPLATE_DINIT}_.
These keys are not defined: {cnfg_external.keys()}."""
        super().__init__(**cnfg)


class _CallPipe(TransformCall):
    def __init__(self, keys_call_imm, keys_call_mut, keys_call_out):
        self.__call_keys_checker = DecsChecker(decs=set(keys_call_imm) | set(keys_call_mut), check_values=False, use_default_values=True)
        self.__call_mut_keys_checker = DecsChecker(decs=keys_call_mut, check_values=True, use_default_values=False, deepcopy_checked_values=True)
        self.__call_out_keys_checker = DecsChecker(decs=keys_call_out, check_values=True, use_default_values=True, deepcopy_checked_values=True)

        self.__call_keys_checker = self._keys_checker_wrapper(
            self.__call_keys_checker, keys_set_name='DCALL', stage_name='before call; input keys vs call keys')
        self.__call_mut_keys_checker = self._keys_checker_wrapper(
            self.__call_mut_keys_checker, keys_set_name='DCALL_MUT', stage_name='before call; imm vs mut call keys')
        self.__call_out_keys_checker = self._keys_checker_wrapper(
            self.__call_out_keys_checker, keys_set_name='DCALL_OUT',stage_name='after call; out call keys')

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
        except Exception as e:
            raise ViolinException('cant deepcopy an object for DCALL_IMM')

        try:
            data_out = super().__call__(**data_call_mut)
        except Exception as e:
            raise e

        try:
            data = self._after(data, data_call_imm, data_out)
        except DecDefaultException as e:
            raise DecDefaultException(parent=self, dec=e.dec, e=e.e)
        except DecCheckException as e:
            raise DecCheckException(parent=self, dec=e.dec, e=e.e)
        return data

    def _keys_checker_wrapper(self, keys_checker: DecsChecker, keys_set_name: DecsChecker, stage_name: DecsChecker):
        def body(**data):
            try:
                data_inn, data_ext = keys_checker(**data)
            except TypeError as e:
                # data_call_out is not a dict
                raise DecsFlowException(
                    not_matched_keys=keys_checker.decs,
                    list_of_name__keys_set=[
                        ('data is not a dict:', type(data)),
                        (keys_set_name, keys_checker.decs),
                    ],
                    flow_stage=stage_name, 
                    transform=self)
            except DecsFlowException as e:
                raise DecsFlowException(
                    not_matched_keys=e.not_matched_keys,
                    list_of_name__keys_set=e.list_of_name__keys_set,
                    flow_stage=stage_name,
                    transform=self,
                )
            return data_inn, data_ext
        return body

    def _before(self, data):
        for x in data.keys():
            if not isinstance(x, str):
                print(x)
                assert False
        data_call, data_ext = self.__call_keys_checker(**data)
        data = data_ext
        data_call_mut, data_call_imm = self.__call_mut_keys_checker(**data_call)
        return data, data_call_imm, data_call_mut

    def _after(self, data, data_call_imm, data_call_out):
        data_call_out, _data = self.__call_out_keys_checker(**data_call_out)
        if len(_data) != 0:
            raise DecsFlowException(
                not_matched_keys=_data,
                list_of_name__keys_set=[
                    ('output call data', data_call_out.keys()),
                    ('DCALL_OUT', self.__call_out_keys_checker.decs),
                ],
                flow_stage='after call; out call keys',
                transform=self,
            )
        common_keys = set(data_call_out.keys()) & set(data.keys())
        assert common_keys == set(), f'Common keys: {common_keys}'
        data.update(data_call_imm)
        data.update(data_call_out)
        assert all([isinstance(x, str) for x in data.keys()])
        return data


class CallPipe(_CallPipe):
    def __init__(self):
        # TODO check decs_SMTH == what class actually has
        keys_call_imm = getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_IMM_)
        keys_call_mut = getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_MUT_)
        keys_call_out = getattr(self, 'decs_'+self._DEC_TEMPLATE_DCALL_OUT_)

        assert keys_call_imm == get_decs(self, self._DEC_TEMPLATE_DCALL_IMM_)
        assert keys_call_mut == get_decs(self, self._DEC_TEMPLATE_DCALL_MUT_)
        assert keys_call_out == get_decs(self, self._DEC_TEMPLATE_DCALL_OUT_)

        try:
            self._check_call_decs(keys_call_imm, keys_call_mut, keys_call_out)
        except DecsFlowException as e:
            raise DecsFlowException(
                not_matched_keys=e.not_matched_keys,
                list_of_name__keys_set=e.list_of_name__keys_set,
                flow_stage='Transform init; call keys',
                transform=self,
            )
        
        super().__init__(
            keys_call_imm=keys_call_imm,
            keys_call_mut=keys_call_mut,
            keys_call_out=keys_call_out,
        )


def get_attrs_template_startswith(cls, template_startswith):
    attrs_names = set()
    for attr_info in inspect.getmembers(cls):
        attr_name = attr_info[0]
        if attr_name.startswith(template_startswith):
            attrs_names.add(attr_name)
    return attrs_names

def dec_preproc_classmethod(func, cls):
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

def get_decs(cls, template_startswith):
    attrs_names = get_attrs_template_startswith(cls, template_startswith)
    decs = set()
    for attr_name in attrs_names:
        v = getattr(cls, attr_name)
        if isinstance(v, Dec):
            assert attr_name[len(template_startswith):] == v, f"{attr_name} != {v} for cls {cls}"
            dec = v
        else:
            assert isinstance(v, tuple), f"{attr_name}: {v}"
            assert len(v) == 2, f"{attr_name}: {v}"
            v = tuple([dec_preproc_classmethod(x, cls) for x in v])  # TODO check x is callable with a single argument
            dec = dec_generator(attr_name, template_startswith, v)
            setattr(cls, attr_name, dec)
        decs.add(dec)
    return decs

def get_DecsFromTupleToDec():
    templates_startswith = TransformInit._DECS_TEMPLATES_DINIT_+TransformCall._DECS_TEMPLATES_DCALL_
    assert isinstance(templates_startswith, tuple), templates_startswith
    assert all([re.match(Dec.DecKey.RE_TEMPLATE_STARTSWITH, x) is not None for x in templates_startswith]), templates_startswith

    class DecsFromTupleToDec(type):
        def __init__(cls, name, bases, attrs):
            for template_startswith in TransformInit._DECS_TEMPLATES_DINIT_+TransformCall._DECS_TEMPLATES_DCALL_:
                decs = get_decs(cls, template_startswith)
                setattr(cls, 'decs_'+template_startswith, decs)
            try:
                TransformCall._check_call_decs(*[getattr(cls, 'decs_'+d) for d in TransformCall._DECS_TEMPLATES_DCALL_])
            except DecsFlowException as e:
                raise DecsFlowException(
                    not_matched_keys=e.not_matched_keys,
                    list_of_name__keys_set=e.list_of_name__keys_set,
                    flow_stage='Transform meta; call keys',
                    transform=cls,
                )
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

    DINIT keys:     check_values=True, use_default_values=True, deepcopy_checked_values=Fals
    DCALL_IMM keys: check_values=Fals, use_default_values=True
    DCALL_MUT keys: check_values=True, use_default_values=True, deepcopy_checked_values=True
    DCALL_OUT keys: check_values=True, use_default_values=True, deepcopy_checked_values=True

    to implement:
    _init(self, **cnfg)
    _call(self, **data)
    """
    decs_DINIT_ = None
    decs_DCALL_IMM_ = None
    decs_DCALL_MUT_ = None
    decs_DCALL_OUT_ = None

    def __init__(self, **cnfg):
        # try:
        InitPipe.__init__(self, **cnfg)
        CallPipe.__init__(self,)
        # except ViolinException as e:
        #     raise ViolinException from None
