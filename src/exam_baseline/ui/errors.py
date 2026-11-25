"""Stable errors shared by UI generation and local preview services."""


class UiError(ValueError):
    def __init__(self, code, message, status=409, details=None):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details

    def payload(self):
        return {"code": self.code, "message": str(self), "details": self.details}
