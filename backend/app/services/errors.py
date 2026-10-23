class ServiceError(Exception):
    status = 400
    kind = "bad_request"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotFound(ServiceError):
    status = 404
    kind = "not_found"


class Conflict(ServiceError):
    status = 409
    kind = "conflict"


class Forbidden(ServiceError):
    status = 403
    kind = "forbidden"
