from violin import Transform, TransformPipeline
from violin import static_declaration
from copy import deepcopy
from violin import checkers as vch


def test_default():
    class T0(Transform):
        def _init(self, **cnfg):
            pass
        def _call(self, **data):
            return {}
    t = T0()
    out = t()
    assert isinstance(out, dict)
    assert len(out.keys())==0

def test0():
    assert Transform.decs_DINIT == set()
    class A(Transform):
        pass
    assert A.decs_DINIT == set()

    assert Transform.decs_DINIT == set()
    assert Transform.decs_DCALL_IMM == set()
    assert Transform.decs_DCALL_MUT == set()
    assert Transform.decs_DCALL_OUT == set()
    class A(Transform):
        pass
    assert A.decs_DINIT == set()
    assert A.decs_DCALL_IMM == set()
    assert A.decs_DCALL_MUT == set()
    assert A.decs_DCALL_OUT == set()

def test1():
    class A(Transform):
        DINIT_smth = (None, None)
    assert A.decs_DINIT == {'smth',}

    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
    assert A.decs_DINIT == {'smth',}
    assert A.decs_DCALL_IMM == {'smth',}

def test2():
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
    try:
        A(**{A.DINIT_smth: 0})
    except Exception:
        pass
    else:
        raise Exception
    
    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_IMM_smth = (None, None)
    assert A.decs_DINIT == {'smth',}
    assert A.decs_DCALL_IMM == {'smth',}

    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_MUT_smth = (None, None)
    assert A.decs_DINIT == {'smth',}
    assert A.decs_DCALL_IMM == {'smth',}
    assert A.decs_DCALL_MUT == {'smth',}  # TODO I wanna detect intersections at a metaclass time
    try:
        A(**{A.DINIT_smth: 0})
    except Exception:
        pass  # TODO not at an init time (look at TODO above)
    else:
        raise Exception

def test3():
    class A(Transform):
        DINIT_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_IMM_smth = (None, None)
        DCALL_MUT_smth = (None, None)
    class B(A):
        pass
    try:
        B(**{B.DINIT_smth: 0})
    except Exception:
        pass
    else:
        raise Exception

def test4():
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

def test5():
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
    out = tp()
    assert out['main_value'] == 0

def test6():
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

def test7():
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

def test8():
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


def test9():
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


def test():
    test0()
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    test8()
    test9()


def main():
    test_default()
    test()
    print(__file__, 'test passed')
