class WRTException(Exception):
    pass


class WRTConfNotFound(WRTException):
    pass


class WRTConfigParamNotFound(WRTException):
    pass


class SwiftConfNotFound(WRTException):
    pass


class WRTRevisionNotFound(WRTException):
    pass


class WRTProjectNotFound(WRTException):
    pass


class WRTUserNotFound(WRTException):
    pass


class WRTRequestFailed(WRTException):
    pass
