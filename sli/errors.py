class SLIException(Exception):
    pass


class InvalidArgumentsException(SLIException):
    pass


class AppSkilletNotFoundException(SLIException):
    pass


class SLILoaderError(SLIException):
    """
    This error should only be called when the -le flag is set, it bypasses
    normal exception handling to ensure it is always raised
    """
    pass
