from app.schemas.cv_content import CVContent, CVEntry

def make_cv_content(**overrides):
    values = {
        'summary': 'Python developer',
        'experience': [],
        'projects': [],
    }

    values.update(overrides)
    return CVContent(**values)

def make_cv_entry(**overrides):
    values = {
        'title': 'Backend developer',
        'bullets': []
    }

    values.update(overrides)
    return CVEntry(**values)


def test_cv_entry_uses_empty_lists_by_default():
    entry = make_cv_entry()

    assert entry.stack == []
    assert entry.bullets == []


def test_cv_entry_empty_lists_by_default():
    content = make_cv_content()

    assert content.location is None


def test_cv_content_as_text_contains_summary_experience_and_projects():
    content = make_cv_content(
        summary="Experienced Python developer",
        experience=[
            make_cv_entry(
                title='Backend Developer',
                bullets=['Built REST API', 'Added tests'],
            )
        ],
        projects=[
            make_cv_entry(
                title='JobFinder',
                bullets=['Created scraper'],
            )
        ]
    )

    text = content.as_text()


    assert "PROFESSIONAL SUMMARY:" in text
    assert "Experienced Python developer" in text
    assert "EXPERIENCE:" in text
    assert "Backend Developer" in text
    assert "- Built REST API" in text
    assert "- Added tests" in text
    assert "PROJECTS:" in text
    assert "JobFinder" in text
    assert "- Created scraper" in text