import test_transform, test_exception
from test_utils import do_test_modules

test_modules = [test_transform, test_exception]


if __name__ == '__main__':
    do_test_modules(test_modules)
