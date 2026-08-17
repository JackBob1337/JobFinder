from pydantic import BaseModel, Field, model_validator

class ATSCheckResult(BaseModel):
    passed: bool
    score: int = Field(ge=0, le=100)
    missing_keywords: list[str] = []
    missing_skills: list[str] = []
    weak_bullets: list[str] = []
    issues: list[str] = []
    recommendations: list[str] = []

    @model_validator(mode='after')
    def validate_passed_matches_score(self):
        expected_passed = self.score >= 75

        if self.passed != expected_passed:
            raise ValueError(
                'passed must be True when score >= and False otherwise'
            )

        return self
    
