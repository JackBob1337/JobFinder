class RepositoryError(Exception):
    """Base exception for repository errors"""

class ForeignKeyViolationError(RepositoryError):
    """Raised whe a foreign key constraint is violated"""

class DatabaseUnavailableError(RepositoryError):
    """Raised when the database connection is unavailable"""