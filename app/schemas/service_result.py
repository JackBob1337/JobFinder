from pydantic import BaseModel, Field, model_validator

class ServiceError(BaseModel):
    item_id: str
    message: str


class ServiceResult(BaseModel):
    total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed: int = Field(ge=0)
    errors: list[ServiceError] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_counts(self):
        if self.succeeded + self.failed != self.total:
            raise ValueError(
                'succeeded  + failed must be equal to total'
            )

        if len(self.errors) != self.failed:
            raise ValueError(
                'errors count must be equal to failed'
            )

        return self