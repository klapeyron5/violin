from violin import Transform, TransformPipeline
from violin import static_declaration
from violin.exception import DecsFlowException
from copy import deepcopy
from violin import checkers as vch


def test_1():
    try:
        class T0(Transform):
            DCALL_IMM_key0 = (None, None)
            DCALL_OUT_key0 = (None, None)
            def _init(self, **cnfg):
                pass
            def _call(self, **data):
                return {}
    except DecsFlowException as e:
        pass
    else:
        raise Exception


def test_2():
    class T0(Transform):
        DCALL_IMM_key0 = (None, None)
        DCALL_MUT_key1 = (None, None)
        DCALL_OUT_key2 = (None, None)
        def _init(self, **cnfg):
            pass
        def _call(self, **data):
            return {}
    T0.decs_DCALL_IMM_ = T0.decs_DCALL_IMM_ | {T0.DCALL_OUT_key2,}
    # TODO decs is not set but tuple or list
    # TODO decs contains not Dec
    try:
        t = T0()
    except DecsFlowException as e:
        assert e.not_matched_keys == {'key2'}
    else:
        raise Exception
