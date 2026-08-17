# app/exceptions.py

class JobHunterError(Exception):
    """Базовое исключение всего проекта"""
    pass


# === DB / Repository layer ===

class RepositoryError(JobHunterError):
    """Базовая ошибка слоя хранения"""
    pass


class DatabaseConnectionError(RepositoryError):
    """БД недоступна или соединение оборвалось"""
    pass


# === Sources layer ===

class SourceError(JobHunterError):
    """Базовая ошибка источников вакансий"""
    pass


class SourceFetchException(SourceError):
    def __init__(self, source_name: str, original_error: Exception) -> None:
        self.source_name = source_name
        self.original_error = original_error
        super().__init__(f"Failed to fetch from {source_name}: {original_error}")


# === Agents layer ===

class AgentError(JobHunterError):
    """Базовая ошибка агентов (LLM-вызовы)"""
    pass


class AnalysisError(AgentError):
    def __init__(self, job_id: int, original_error: Exception):
        self.job_id = job_id
        self.original_error = original_error
        super().__init__(f"Failed to analyze job {job_id}: {original_error}")


class FilterError(AgentError):
    def __init__(self, job_id: int, original_error: Exception):
        self.job_id = job_id
        self.original_error = original_error
        super().__init__(f"Failed to filter job {job_id}: {original_error}")


class TailorError(AgentError):
    def __init__(self, job_id: int, original_error: Exception):
        self.job_id = job_id
        self.original_error = original_error
        super().__init__(f"Failed to tailor CV for job {job_id}: {original_error}")


class LLMRateLimitError(AgentError):
    """Упёрлись в rate limit провайдера (OpenAI/Groq)"""
    pass


# === Services layer ===

class ServiceError(JobHunterError):
    """Базовая ошибка сервисного слоя (оркестрация)"""
    pass


class PipelineStageError(ServiceError):
    """Целая стадия пайплайна (analyze/filter/tailor) провалилась критично"""
    pass