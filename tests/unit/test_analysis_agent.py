from app.agents.analysis_agent import safe_parse_years

def test_safe_parse_years_none_for_none():
    assert safe_parse_years(None) is None


def test_safe_parse_years_returns_integer_unchanged():
    assert safe_parse_years(5) == 5


def test_safe_parse_years_extracts_number_from_text():
    assert safe_parse_years('3 years of experience') == 3
    assert safe_parse_years('At least 5 years') == 5


def test_parse_years_returns_none_when_text_has_no_number():
    assert safe_parse_years('several years of experience') is None


def test_safe_parse_years_returns_none_for_unsupported_type():
    assert safe_parse_years(3.6) is None
    assert safe_parse_years([]) is None