import traceback, inspect


def wrap_test(testfunc):
    try:
        testfunc()
        return 0
    except Exception as e:
        modulename = inspect.getmodule(testfunc).__name__
        funcname = testfunc.__name__
        print(f'ERROR in {modulename}.{funcname}')
        print('Exception type:', type(e))
        print('Exception txt:', str(e))
        print('traceback:', traceback.print_exc())
    return 1


def do_test_module(test_module):
    all_i = 0
    failed_i = 0
    for testfunc_name in dir(test_module):
        if testfunc_name.startswith('test_'):
            testfunc_instance = getattr(test_module, testfunc_name)
            out = wrap_test(testfunc_instance)
            all_i += 1
            if out == 1:
                failed_i += 1
            else:
                assert out == 0
    return all_i, failed_i


def do_test_modules(test_modules):
    All_i, Failed_i = 0, 0
    for test_module in test_modules:
        all_i, failed_i = do_test_module(test_module)
        All_i += all_i
        Failed_i += failed_i
    print('--------------------------')
    print(f'{Failed_i}/{All_i} tests failed')
    if failed_i != 0:
        raise Exception('Tests failed!') from None
    else:
        print('Tests passed!')
