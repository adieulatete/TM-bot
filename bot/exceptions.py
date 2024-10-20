class PastDateError(Exception):
    """Raised when the user inputs a date that is in the past."""
    def __init__(self, message="Дата не может быть в прошлом."):
        super().__init__(message)
