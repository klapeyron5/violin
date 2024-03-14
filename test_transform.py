from violin import Transform, TransformPipeline
from violin import static_declaration
from copy import deepcopy
import traceback
from violin import checkers as vch


def test_0():
    class T0(Transform):
        def _init(self, **cnfg):
            pass
        def _call(self, **data):
            return {}
    t = T0()
    out = t()
    assert isinstance(out, dict)
    assert len(out.keys())==0

def test_1():
    assert Transform.decs_DINIT_ == set()
    class A(Transform):
        pass
    assert A.decs_DINIT_ == set()

    assert Transform.decs_DINIT_ == set()
    assert Transform.decs_DCALL_IMM_ == set()
    assert Transform.decs_DCALL_MUT_ == set()
    assert Transform.decs_DCALL_OUT_ == set()
    class A(Transform):
        pass
    assert A.decs_DINIT_ == set()
    assert A.decs_DCALL_IMM_ == set()
    assert A.decs_DCALL_MUT_ == set()
    assert A.decs_DCALL_OUT_ == set()

def test_2():
    class A(Transform):
        DINIT_smth = (None, None)
    assert A.decs_DINIT_ == {'smth',}

    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
    assert A.decs_DINIT_ == {'smth',}
    assert A.decs_DCALL_IMM_ == {'smth',}

def test_3():
    class A(Transform):
        @staticmethod
        def f(x):
            assert True
        DINIT_smth = (None, None)
        DINIT_smth = (f, None)
        def _init(self, **config):
            pass
    A(**{A.DINIT_smth: 0})

    class A(Transform):
        @staticmethod
        def f(x):
            assert False
        DINIT_smth = (None, None)
        DINIT_smth = (f, None)
        def _init(self, **config):
            pass
    try: A(**{A.DINIT_smth: 0})
    except Exception: pass
    else: raise
    
    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_IMM_smth = (None, None)
    assert A.decs_DINIT_ == {'smth',}
    assert A.decs_DCALL_IMM_ == {'smth',}

    try:
        class A(Transform):
            DINIT_smth = (None, None)
            DCALL_IMM_smth = (None, None)
            DCALL_IMM_smth = (None, None)
            DCALL_MUT_smth = (None, None)
    except Exception: pass
    else: raise

def test_4():
    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
    class B(A):
        pass
    try: 
        B(**{B.DINIT_smth: 0})
    except Exception:
        pass
    else: 
        raise

    class B(A):
        def _init(self, **config):
            pass
    b = B(**{B.DINIT_smth: 0})
    try:
        b(**{B.DCALL_IMM_smth: 0})
    except Exception: pass
    else: raise

    class B(A):
        def _init(self, **config):
            pass
        def _call(self, **data):
            pass
    b = B(**{B.DINIT_smth: 0})
    try:
        b(**{B.DCALL_IMM_smth: 0})
    except TypeError: pass  # TODO should write proper error msg about not returning dict from _call
    else: raise

    class B(A):
        def _init(self, **config):
            pass
        def _call(self, **data):
            return {}
    b = B(**{B.DINIT_smth: 0})
    b(**{B.DCALL_IMM_smth: 0})

def test_5():
    class A(Transform):
        @classmethod
        def check(self, x):  # TODO couldn't use self method now !
            assert x == 19
        DINIT_smth = (None, None)
        DINIT_smth0 = (None, None)
        DCALL_IMM_smth = (check, None)
        DCALL_MUT_smth0 = (check, None)
        def _init(self, smth, smth0):
            self.smth = smth
        def _call(self, smth, smth0):
            assert smth0==19
            return {}
    a = A(**{
        A.DCALL_IMM_smth: 19,
        A.DCALL_MUT_smth0: 19,
    })
    a(**{
        A.DCALL_IMM_smth: 19,
        A.DCALL_MUT_smth0: 19,
    })
    a(**{
        A.DINIT_smth: 19,
        A.DINIT_smth0: 19,
    })

    a(**{
        A.DCALL_IMM_smth: 0,  # TODO IMM keys are unchecked now, should use wrapper for in-out IMM keys checking
        A.DCALL_MUT_smth0: 19,
    })
    a(**{
        A.DINIT_smth: 0,
        A.DINIT_smth0: 19,
    })
    try:
        a(**{
            A.DCALL_IMM_smth: 0,
            A.DCALL_MUT_smth0: 1,
        })
    except Exception: pass
    else: raise

def test_6():
    class A(Transform):
        VAR = 9
        VAR0 = 99
        
        @classmethod
        def check_is_video(cls, x):
            assert x != cls.VAR
        
        @staticmethod
        def check0(x):
            assert x != A.VAR0
        
        DINIT_smth = (check_is_video, None)
        DINIT_smth0 = (check0, None)
        
        def _init(self, **config):
            self.x = config[self.DINIT_smth]

    a = A(**{A.DINIT_smth: 8, A.DINIT_smth0: 0})
    assert a.x==8
    try:
        A(**{A.DINIT_smth: 9, A.DINIT_smth0: 0})
    except Exception:
        pass
    else:
        raise Exception
    
    class B(A):
        VAR = 8
        VAR0 = 88
    a = B(**{B.DINIT_smth: 7, B.DINIT_smth0: 0})
    assert a.x==7
    try:
        B(**{B.DINIT_smth: 9, B.DINIT_smth0: 0})
    except Exception:
        pass
    else:
        raise Exception
    B(**{B.DINIT_smth: 0, B.DINIT_smth0: 88})
    try:
        B(**{B.DINIT_smth: 0, B.DINIT_smth0: 99})
    except Exception:
        pass
    else:
        raise Exception
    B(**{A.DINIT_smth: 8, A.DINIT_smth0: 88})

def test_7():
    def check_main_value(x):
        assert -1<=x<=1

    class InputValue(Transform):
        DCALL_MUT_main_value = (check_main_value, lambda: 0)
        DCALL_OUT_main_value = DCALL_MUT_main_value

        def _init(self, **config):
            pass
        def _call(self, **data):
            return data
    iv = InputValue()
    out = iv(**{iv.DCALL_MUT_main_value: 0.4})
    assert out[iv.DCALL_OUT_main_value] == 0.4
    
    tp = TransformPipeline(**{
        TransformPipeline.DINIT_transforminstances: [
            InputValue(),
        ],
    })
    out = tp(**{
        InputValue.DCALL_MUT_main_value: 0.1,
    })
    assert out['main_value'] == 0.1
    # ------------------------------------------------------
    tp = TransformPipeline(**{
        TransformPipeline.DINIT_transforminstances: [
            InputValue(),
        ],
    })
    out = tp()  # default value
    assert out['main_value'] == 0

def test_8():
    class InputValue(Transform):
        @classmethod
        def check_main_value(cls, x):
            assert -1<=x<=1, x

        DCALL_IMM_main_value_imm = (check_main_value, lambda: 0)
        DCALL_MUT_main_value = (check_main_value, lambda: 0)
        DCALL_OUT_main_value = DCALL_MUT_main_value

        def _init(self, **config):
            pass
        def _call(self, **data):
            return {
                self.DCALL_OUT_main_value: data[self.DCALL_MUT_main_value],
            }
    out = InputValue()(**{
        InputValue.DCALL_IMM_main_value_imm: 0.5,
        InputValue.DCALL_MUT_main_value: 0.4,
    })
    
    try:
        out = InputValue()(**{
            InputValue.DCALL_IMM_main_value_imm: 97,
            InputValue.DCALL_MUT_main_value: 100,
        })
    except Exception:
        pass
    else:
        raise Exception

    class Add(Transform):
        DCALL_IMM_main_value = InputValue.DCALL_MUT_main_value
        DCALL_OUT_modified_value = (InputValue.check_main_value, None)

        def _init(self, **config):
            pass
        def _call(self, **data):
            v = data[self.DCALL_IMM_main_value]
            v += 0.01
            return {
                self.DCALL_OUT_modified_value: v,
            }
    tp = TransformPipeline(**{
        TransformPipeline.DINIT_transforminstances: [
            InputValue(),
            Add(),
        ],
    })
    out = tp(**{
        InputValue.DCALL_IMM_main_value_imm: 97,
        InputValue.DCALL_MUT_main_value: 0.1,
    })
    assert out['main_value_imm'] == 97
    assert out['main_value'] == 0.1
    assert out['modified_value'] == 0.11
    
    out = tp()
    assert out['main_value_imm'] == 0
    assert out['main_value'] == 0
    assert out['modified_value'] == 0.01

def test_9():
    class A(Transform):
        DCALL_IMM_var0 = (None, None)
        DCALL_MUT_var1 = (None, None)

        def _init(self, **cnfg):
            pass

        def _call(self, var0, var1):
            assert var0+var1 == 5
            return {}
    A()(**{
        A.DCALL_IMM_var0: 1,
        A.DCALL_MUT_var1: 4,
    })

def test_10():
    class A(Transform):
        DCALL_IMM_var0 = (None, None)
        DCALL_MUT_var1 = (None, None)

        def _init(self, **cnfg):
            pass

        def _call(self, var0, var1):
            assert var0+var1 == 5
            return {}
    A()(**{
        A.DCALL_IMM_var0: 1,
        A.DCALL_MUT_var1: 4,
    })

    class B(Transform):
        @staticmethod
        def f(x):
            assert isinstance(x, static_declaration.Dec)
        DCALL_IMM_test = (f, None)
        
        def _init(self, **cnfg):
            pass

        def _call(self, test):
            return {}
    
    B()(**{
        B.DCALL_IMM_test: A.DCALL_IMM_var0,
    })


def test_11():
    d = static_declaration.dec_generator('DCALL_IMM_keykey', 'DCALL_IMM_', (vch.nullable(vch.is_str_not_empty), None))
    deepcopy(d)

    class A(Transform):
        @staticmethod
        def check(x):
            pass
        AA = check
    deepcopy(A.check)
    deepcopy(A.AA)

    class A(Transform):
        @staticmethod
        def check(x):
            pass
        DCALL_IMM_keykey = (check, None)
    deepcopy(A.DCALL_IMM_keykey)


def test_12():
    class A(Transform):
        @staticmethod
        def check(x):
            assert isinstance(x, list)
            x.append(113)

        DINIT_x0 = (check, None)
        
        DCALL_IMM_x0 = (check, None)
        DCALL_MUT_x1 = (check, None)
        DCALL_OUT_x1 = (check, None)

        def _init(self, x0):
            self.x0 = x0

        def _call(self, x0, x1):
            return dict(x1=x1)
    x0 = [0,1,2]
    a = A(**{A.DINIT_x0: deepcopy(x0)})
    assert a.x0 == x0+[113,]
    x0 = [0,1,2]
    x1 = [1,2,3]
    out = a(**{
        a.DCALL_IMM_x0: deepcopy(x0),
        a.DCALL_MUT_x1: deepcopy(x1),
    })
    assert out[A.DCALL_IMM_x0] == x0
    assert out[A.DCALL_OUT_x1] == x1


def test_13():
    class A(Transform):
        DCALL_IMM_key0 = (None, None)
    
    class B(Transform):
        DCALL_IMM_key0 = A.DCALL_IMM_key0
    
    try:
        class B(Transform):
            DCALL_IMM_key1 = A.DCALL_IMM_key0
    except Exception: pass
    else: raise


def test_14():
    # test default value exception traceback
    def check_main_value(x):
        assert -1<=x<=1
    
    def default_value():
        raise Exception('hello')

    class InputValue(Transform):
        DCALL_MUT_main_value = (check_main_value, default_value)
        DCALL_OUT_main_value = DCALL_MUT_main_value

        def _init(self, **config):
            pass
        def _call(self, **data):
            return data
    
    tp = InputValue()
    try:
        out = tp()
    except Exception as e:
        print()
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
        # print('traceback:', traceback.print_exc())
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
