from pydantic import BaseModel, Field, model_validator


class ResultError(BaseModel):
    item_id: str
    message: str


class OperationResult(BaseModel):
    total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    skipped: int = Field(default=0, ge=0)
    failed: int = Field(ge=0)
    errors: list[ResultError] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_counts(self):
        if self.succeeded + self.skipped + self.failed != self.total:
            raise ValueError(
                'succeeded + skipped + failed must be equal to total'
            )

        if len(self.errors) != self.failed:
            raise ValueError(
                'errors count must be equal to failed'
            )

        return self


class RepositoryResult(OperationResult):
     """Result of a repository batch operation."""


class ServiceResult(OperationResult):
    """Result of a service operation."""

class PipelineResult(BaseModel):
    scrapped: ServiceResult
    analyzed: ServiceResult
    filtered: ServiceResult