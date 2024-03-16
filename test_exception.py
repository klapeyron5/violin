from violin import Transform, TransformPipeline
from violin import static_declaration
from violin.exception import DecsFlowException
from copy import deepcopy
import traceback
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


def wrap_test(test):
    try:
        test()
        return 0
    except Exception as e:
        print(f'ERROR in {test.__name__}')
        print('Exception type:', type(e))
        print('Exception txt:', str(e))
        print('traceback:', traceback.print_exc())
    return 1


def test():
    all_i = 0
    failed_i = 0
    for f in globals():
        if f.startswith('test_'):
            out = wrap_test(globals()[f])
            all_i += 1
            if out == 1:
                failed_i += 1
            else:
                assert out == 0
    return all_i, failed_i


def main():
    all_i, failed_i = test()
    print('--------------------------')
    print(f'{failed_i}/{all_i} tests failed')
    print(__file__)
    if failed_i != 0:
        raise Exception('Tests failed!') from None
    else:
        print('Tests passed!')
