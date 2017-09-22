class PRException(Exception):
    pass

class PrivateLeagueException(PRException):
    pass

class InvalidLeagueException(PRException):
    pass

class UnknownLeagueException(PRException):
    pass

class AuthorizationError(PRException):
    pass
