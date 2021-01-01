# Some general definitions
class FunctionCalledException(Exception):
    pass


def function_called_raiser(*args, **kwargs):
    raise FunctionCalledException()

