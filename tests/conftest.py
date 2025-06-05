import os
from unittest import mock

import pytest

from terndata.flux import utils

current_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def session_mock(monkeypatch):
    """Mock utils.session.get method for testing purposes."""

    # the mock instance to replace `utils.session.get` function
    session_get_mock = mock.MagicMock()
    # inject our wrapped or mocked connection
    monkeypatch.setattr(utils.session, "get", session_get_mock)
    # monkeypatch.setattr("terndata.flux.utils.session.get", session_get_mock)
    return session_get_mock


@pytest.fixture
def dataset_urls_mock(monkeypatch):
    """Mock utils.get_dataset_urls method."""

    def mocked_dataset_urls(site, *args, **kw):
        if site == "Warra":
            # Daily dataset
            return {"daily": os.path.join(current_dir, f"data/{site}_daily_test.nc")}
        # 30min dataset
        return {"30min": os.path.join(current_dir, f"data/{site}_test.nc")}

    ds_urls_mock = mock.MagicMock()
    ds_urls_mock.side_effect = mocked_dataset_urls
    monkeypatch.setattr("terndata.flux.flux_api.get_dataset_urls", ds_urls_mock)
    return ds_urls_mock


@pytest.fixture
def get_versions_mock(monkeypatch):  # noqa: PT004
    """Mock flux_api.get_versions method."""
    version_mock = mock.MagicMock()
    version_mock.return_value = ["2024_v2"]
    monkeypatch.setattr("terndata.flux.flux_api.get_versions", version_mock)
