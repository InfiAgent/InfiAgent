class DependencyException(Exception):
    pass


class InputErrorException(Exception):
    pass


class InternalErrorException(Exception):
    pass


class DatabaseException(DependencyException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class SandboxException(DependencyException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class LLMException(DependencyException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class ModelMaxIterationsException(DependencyException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class InvalidConfigException(InputErrorException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class SandBoxFileUploadException(SandboxException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)


class PluginException(DependencyException):
    def __init__(self, message, *args: object):
        super().__init__(message, *args)

