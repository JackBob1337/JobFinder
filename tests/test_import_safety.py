import importlib


def test_production_modules_import_without_running_workflows() -> None:
    nofluffjobs = importlib.import_module("app.sources.nofluffjobs")
    cli_entrypoint = importlib.import_module("main")

    assert nofluffjobs.NoFluffJobsSource.__name__ == "NoFluffJobsSource"
    assert callable(cli_entrypoint.main)
