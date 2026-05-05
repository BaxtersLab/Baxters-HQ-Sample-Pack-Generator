class BSPGError(Exception):
    """Base exception for BSPG"""
    pass


class ConfigError(BSPGError):
    def __init__(self, message: str = ''):
        self.message = message
        super().__init__(message)


class PathError(BSPGError):
    def __init__(self, path: str = '', message: str = ''):
        self.path = path
        self.message = message
        super().__init__(message)


class BackendError(BSPGError):
    def __init__(self, exit_code: int | None = None, stderr: str | None = None, message: str = ''):
        self.exit_code = exit_code
        self.stderr = stderr
        self.message = message
        super().__init__(message)


class FlowchartError(BSPGError):
    def __init__(self, checkboxes: dict | None = None, message: str = ''):
        self.checkboxes = checkboxes or {}
        self.message = message
        super().__init__(message)


class HRTError(BSPGError):
    def __init__(self, status: str | None = None, message: str = ''):
        self.status = status
        self.message = message
        super().__init__(message)


class GUIError(BSPGError):
    def __init__(self, component: str = '', message: str = ''):
        self.component = component
        self.message = message
        super().__init__(message)


class ValidationError(BSPGError):
    def __init__(self, field: str = '', message: str = ''):
        self.field = field
        self.message = message
        super().__init__(message)
