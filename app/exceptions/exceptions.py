class SourceFetchException(Exception):
    def __init__(self, source_name: str, cause: Exception):
        self.source_name = source_name
        self.cause = cause
        super().__init__(
            f'Failed to fetch jobs from {source_name}: {cause}'
        )

class TransientSourceFetchException(SourceFetchException):
    """Timeout, transport failure, 408/425/429 or selected 5xx."""


class InvalidSourcePayloadException(SourceFetchException):
    """Provider returned malformed or incompatible data."""


class SourceConfigurationException(SourceFetchException):
    """Required source configuration is missing or invalid."""


class RepositoryError(Exception):
    """Base exception for repository errors."""


class DatabaseConnectionError(RepositoryError):
    """Raised when the database is unavailable."""


class DatabaseUnavailableError(DatabaseConnectionError):
    """Raised when the database connection is unavailable."""


class ForeignKeyViolationError(RepositoryError):
    """Raised when a foreign key constraint is violated."""

class FilterError(Exception):
    """Raised when job filtering fails."""