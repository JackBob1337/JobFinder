from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class HttpPolicy:
    timeout_seconds: float = 15.0
    attempts: int = 3


@dataclass(frozen=True, slots=True)
class ArbeitnowSearch:
    visa_sponsorship: bool | None = None


@dataclass(frozen=True, slots=True)
class JustJoinItSearch:
    category: str = 'python'
    experience_levels: tuple[str, ...] = ('junior',)
    location: str = 'all-locations'
    max_items: int = 100


@dataclass(frozen=True, slots=True)
class JustJoinItPolicy:
    request_timeout_seconds: float = 30.0
    actor_timeout_seconds: float = 300.0
    dataset_timeout_seconds: float = 60.0
    client_max_retries: int = 4


@dataclass
class NoFluffJobsSearch:
    query: str = "python"
    page_size: int = 100
    max_pages: int | None = None
    salary_currency: str = "PLN"
    salary_period: str = "month"
    region: str = "pl"
    language: str = "pl-PL"
    seniority: tuple[str, ...] = ("Junior",)