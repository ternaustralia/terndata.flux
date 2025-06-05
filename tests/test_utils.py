import os

from requests.exceptions import HTTPError

from terndata.flux import utils

current_dir = os.path.dirname(os.path.abspath(__file__))


def mocked_response(resp_text=None, status_code=200):
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text = text_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code != 200:
                raise HTTPError(f"Error: response fail with {self.status_code}")

    return MockResponse(resp_text, status_code)


def test_get_catalog_url():
    # Tests that correct catalog url is returned for different object types
    url = "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/{}catalog.xml"
    test_items = [
        ("site", {}, url.format("")),
        ("version", {"site": "AdelaideRiver"}, url.format("AdelaideRiver/")),
        (
            "processing_level",
            {"site": "AdelaideRiver", "version": "2024_v3"},
            url.format("AdelaideRiver/2024_v3/"),
        ),
        (
            "dataset",
            {"site": "AdelaideRiver", "version": "2024_v5", "processing_level": "L3"},
            url.format("AdelaideRiver/2024_v5/L3/default/"),
        ),
    ]

    for obj, param, expected_url in test_items:
        assert utils.get_catalog_url(obj, params=param) == expected_url


def test_get_catalog_items_site_catalog_url(session_mock):
    # Test get site catalog urls from site catalog page
    url = "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/catalog.xml"

    with open(os.path.join(current_dir, "data/site_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())

    items = utils.get_catalog_items(url, itype="catalogRef")

    # Check that the site catalog urls are as expected
    assert set(items.keys()) == {"AdelaideRiver", "WallabyCreek"}
    assert (
        items.get("AdelaideRiver")
        == "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/AdelaideRiver/catalog.xml"
    )
    assert (
        items.get("WallabyCreek")
        == "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/WallabyCreek/catalog.xml"
    )


def test_get_catalog_items_dataset_catalog_url(session_mock):
    # Test get dataset urls from dataset catalog page
    url = "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/AdelaideRiver/2024_v2/L3/default/catalog.xml"

    with open(os.path.join(current_dir, "data/dataset_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())

    items = utils.get_catalog_items(url, itype="dataset")

    # Check that the dataset urls are as expected
    assert set(items.keys()) == {"30min"}
    assert (
        items.get("30min")
        == "https://dap.tern.org.au/thredds/dodsC/ecosystem_process/ozflux/AdelaideRiver/2024_v2/L3/default/AdelaideRiver_L3.nc"
    )


def test_get_dataset_urls(session_mock):
    # Test get dataset url
    with open(os.path.join(current_dir, "data/dataset_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())

    urls = utils.get_dataset_urls("AdelaideRiver", "new_version", "L3")

    # Check that the dataset urls are as expected
    assert set(urls.keys()) == {"30min"}
    assert (
        urls.get("30min")
        == "https://dap.tern.org.au/thredds/dodsC/ecosystem_process/ozflux/AdelaideRiver/new_version/L3/default/AdelaideRiver_L3.nc"
    )
