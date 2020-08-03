class APIKeyError(Exception):
    pass


# Request exceptions
class RequestException(Exception):
    pass

class InvalidRequest(RequestException):
    pass

class FailedRequest(RequestException):
    pass


# Session exceptions
class SessionError(RequestException):
    pass

class InvalidSessionError(SessionError):
    pass

class NoSessionError(SessionError):
    pass

class ExhaustedAttemptsException(Exception):
    pass
