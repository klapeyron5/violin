# Dec == declaration
# Dec is class static variable: D<PREFIX>_<name> = (value_checker: callable(x)->None, default_value: callable()->x)
# default_value is not necessary
import inspect, re


def get_function_arguments(f):
    if inspect.isfunction(f) or inspect.ismethod(f) or isinstance(f, classmethod) or isinstance(f, staticmethod):
        assert inspect.isroutine(f)
        if isinstance(f, classmethod) or isinstance(f, staticmethod):
            f = f.__func__
        # print(hasattr(f, '__self__'), )
        # args = inspect.getattr_static(f)
        sig = inspect.signature(f)
        args = list(sig.parameters.keys())
        if len(args)>0 and args[0] in ('self', 'cls'):
            args = args[1:]
        return args
    else:
        assert not inspect.isroutine(f)
        return None


def dec_generator(dec_key, dec_key_template_startswith, dec_val):
    cls = Dec
    dec_key = cls.DecKey.preproc(dec_key, dec_key_template_startswith)
    return Dec(dec_key, dec_val)


class Dec(str):
    def __new__(cls, dec_key, *args, **kwargs):#dec_key_template_startswith, dec_val):
        instance = str.__new__(cls, dec_key)
        return instance
    
    def __init__(self, dec_key, dec_val):
        self.value_checker, self.default_value = self.DecVal.preproc(dec_val)
    
    class DecKey:
        PREFIX = 'D'
        RE_TEMPLATE_STARTSWITH = '^'+PREFIX+'[A-Z0-9]{1,}_([A-Z0-9]{1,}_){0,}'
        RE_TEMPLATE_NAME = '[a-zA-Z0-9]{1,}(_[a-zA-Z0-9]{1,}){0,}$'
        @classmethod
        def preproc(cls, dec_key, dec_key_template_startswith):
            assert isinstance(dec_key, str) and dec_key!=''
            assert isinstance(dec_key_template_startswith, str) and dec_key_template_startswith!=''
            assert dec_key_template_startswith==dec_key[:len(dec_key_template_startswith)]
            assert re.match(cls.RE_TEMPLATE_STARTSWITH+'$', dec_key[:len(dec_key_template_startswith)]) is not None
            dec_key = dec_key[len(dec_key_template_startswith):]
            assert re.match('^'+cls.RE_TEMPLATE_NAME, dec_key) is not None
            return dec_key
    
    class DecVal:
        @classmethod
        def preproc(cls, dec_val):
            assert isinstance(dec_val, tuple)
            value_checker, default_value = dec_val
            value_checker = cls._preproc_value_checker(value_checker)
            default_value = cls._preproc_default_value(default_value)
            return value_checker, default_value
        
        @classmethod
        def _preproc_value_checker(cls, value_checker):
            if value_checker is None:
                value_checker = lambda x: x
            else:
                func_args = get_function_arguments(value_checker)
                # assert len(func_args)==1  TODO
            return value_checker
        
        @classmethod
        def _preproc_default_value(cls, default_value):
            if default_value is None:
                def r():
                    raise Exception('No default value for missing data key.')
                default_value = lambda: r()
            else:
                func_args = get_function_arguments(default_value)
                # assert len(func_args)==0  TODO
            return default_value


class DecsChecker:
    def __init__(self, decs: set, check_values=True, use_default_values=False):
        assert isinstance(decs, set)
        assert all([isinstance(x, Dec) for x in decs])
        self.decs = decs

        if check_values and use_default_values:
            self._decs_process = self._f3
        elif check_values and not use_default_values:
            self._decs_process = self._f2
        elif not check_values and use_default_values:
            self._decs_process = self._f1
        elif not check_values and not use_default_values:
            self._decs_process = self._f0
        else:
            raise NotImplementedError

    def __call__(self, **data):
        data_internal, data_external = {}, {}
        for k in self.decs:
            try:
                assert isinstance(k, Dec)
                self._decs_process(k, data)
                data_internal[k] = data[k]
                del data[k]
            except KeyError:
                errmsg = f"""ERROR: {k} not in kwargs
self.decs: {[str(x) for x in self.decs]}
kwargs.keys(): {data.keys()}
"""
                raise KeyError(errmsg)
            except Exception as e:
                raise Exception(f"{str(e)}\nDecKey: {k}.")
        data_external = data
        return data_internal, data_external

    @classmethod
    def _f0(cls, dec: Dec, data: dict):
        pass
    @classmethod
    def _f1(cls, dec: Dec, data: dict):
        if dec not in data:
            data[dec] = dec.default_value()
            cls._f2(dec, data)  # check default value
    @classmethod
    def _f2(cls, dec: Dec, data: dict):
        dec.value_checker(data[dec])
    @classmethod
    def _f3(cls, dec: Dec, data: dict):
        if dec not in data:
            data[dec] = dec.default_value()
        cls._f2(dec, data)
