# Testing using TERN THREDD server at dap.tern.org.au.

import os
import tempfile
from datetime import datetime

import numpy as np
import pytest
from requests.exceptions import HTTPError

from terndata import flux

current_dir = os.path.dirname(os.path.abspath(__file__))


def mocked_response(resp_text=None, status_code=200):
    # Mocked response object
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text = text_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code != 200:
                raise HTTPError(f"Error: response fail with {self.status_code}")

    return MockResponse(resp_text, status_code)


def test_get_sites(session_mock, get_versions_mock, dataset_urls_mock):
    """Test get all the sites."""
    with open(os.path.join(current_dir, "data/site_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())
    sites = flux.get_sites()
    assert len(sites) == 2
    assert set(sites["site"].to_list()) == {"AdelaideRiver", "WallabyCreek"}


def test_get_versions(session_mock):
    with open(os.path.join(current_dir, "data/version_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())
    versions = flux.get_versions("AdelaideRiver")
    assert set(versions) == {"2024_v1", "2024_v2"}


def test_get_versions_bad_input(session_mock):
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_versions("bad-site-name")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith("Error: fail to get versions for site 'bad-site-name'")


def test_get_processing_levels(session_mock):
    with open(os.path.join(current_dir, "data/processing_level_catalog.xml")) as f1:
        session_mock.return_value = mocked_response(f1.read())
    pro_levels = flux.get_processing_levels("AdelaideRiver", "2024_v2")
    assert set(pro_levels) == {"L3", "L6"}


def test_get_processing_levels_bad_input(session_mock):
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_processing_levels("AdelaideRiver", "bad-version")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get processing-levels for site 'AdelaideRiver', version 'bad-version'"
    )


def test_get_global_attributes(dataset_urls_mock):
    attributes = flux.get_global_attributes("AdelaideRiver", "2024_v2")
    assert attributes["site_name"] == "Adelaide River"
    assert set(attributes.keys()) == {
        "Conventions",
        "acknowledgement",
        "canopy_height",
        "comment",
        "contact",
        "coverage_flux_L3",
        "coverage_meteorology_L3",
        "coverage_radiation_L3",
        "coverage_soil_L3",
        "data_link",
        "date_created",
        "featureType",
        "fluxnet_id",
        "history",
        "institution",
        "latitude",
        "license",
        "license_name",
        "longitude",
        "metadata_link",
        "nc_nrecs",
        "ozflux_link",
        "processing_level",
        "publisher_name",
        "pyfluxpro_version",
        "python_version",
        "references",
        "site_name",
        "site_pi",
        "soil",
        "source",
        "time_coverage_end",
        "time_coverage_start",
        "time_step",
        "time_zone",
        "title",
        "tower_height",
        "vegetation",
        "DODS.strlen",
        "DODS.dimName",
    }


def test_get_variables(dataset_urls_mock):
    variables = flux.get_variables("AdelaideRiver", "2024_v2")
    assert set(variables) == {
        "AH",
        "CO2",
        "Flu",
        "AH_QCFlag",
        "CO2_QCFlag",
        "Flu_QCFlag",
        "time",
        "longitude",
        "latitude",
    }


def test_get_temporal_range(dataset_urls_mock):
    start, end = flux.get_temporal_range("AdelaideRiver", "2024_v2")
    assert start == "2007-10-17T11:30:00.000000000"
    assert end == "2007-10-20T11:00:00.000000000"


def test_get_coordinates(dataset_urls_mock):
    coord_names = flux.get_coordinates("AdelaideRiver", "2024_v2")
    assert set(coord_names) == {"time", "latitude", "longitude"}


def test_get_dataset(dataset_urls_mock):
    # Test get dataset
    ds = flux.get_dataset("AdelaideRiver", "2024_v2", "L3")
    assert ds.attrs.get("site_name") == "Adelaide River"
    fill_count = int(np.sum((ds["AH"] == -9999)).values)
    na_count = int(np.sum(np.isnan(ds["AH"])).values)
    assert fill_count > 0
    assert na_count == 0

    # set missing value in dataset to nan.
    ds2 = flux.get_dataset("AdelaideRiver", "2024_v2", "L3", missing_as_nan=True)
    fill_count2 = int(np.sum((ds2["AH"] == -9999)).values)
    na_count2 = int(np.sum(np.isnan(ds2["AH"])).values)
    assert fill_count2 == 0
    assert na_count2 == fill_count


def test_get_dataset_bad_input(dataset_urls_mock):
    # Test get_dataset with bad site name
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_dataset("bad-site-name", "2024_v2", "L3")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get dataset for site 'bad-site-name', version '2024_v2', "
        "processing-level 'L3'"
    )


def test_get_subset(dataset_urls_mock):
    # Test get subset
    subset = flux.get_subset(
        "AdelaideRiver",
        "2024_v2",
        processing_level="L3",
        variables=["AH", "Flu"],
        start=datetime.strptime("2007-10-18 01:30", "%Y-%m-%d %H:%M"),  # noqa: DTZ007
        end=datetime.strptime("2007-10-19 00:00", "%Y-%m-%d %H:%M"),  # noqa: DTZ007
    )
    assert set(subset.variables) == {
        "AH",
        "Flu",
        "AH_QCFlag",
        "Flu_QCFlag",
        "time",
        "longitude",
        "latitude",
    }
    assert subset.attrs["site_name"] == "Adelaide River"
    assert str(subset.coords["time"].data[0]) == "2007-10-18T01:30:00.000000000"
    assert str(subset.coords["time"].data[-1]) == "2007-10-19T00:00:00.000000000"


def test_get_subset_bad_variable(dataset_urls_mock):
    # Test get_subset with bad variable
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_subset("AdelaideRiver", "2024_v2", "L3", variables=["AH", "bad-var"])
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get subset for site 'AdelaideRiver': variable 'bad-var' not found"
    )


def test_get_subset_bad_processing_level(session_mock):
    # Test get_subset with bad processing-level
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_subset("AdelaideRiver", "2024_v2", "bad-level", variables=["AH", "Flu"])
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get dataset for site 'AdelaideRiver', version '2024_v2', "
        "processing-level 'bad-level'"
    )


def test_get_l6_dataset(dataset_urls_mock):
    ds = flux.get_l6_dataset("Warra", "2024_v2", ds_type="daily")
    assert ds.attrs.get("site_name") == "Warra"
    assert ds.attrs.get("time_step") == "daily"


def test_get_l6_dataset_bad_sitename(session_mock):
    # Test get L6 dataset with bad site name
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_l6_dataset("bad-site-name", "2024_v2", ds_type="daily")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get L6 dataset for site 'bad-site-name', version '2024_v2'"
    )


def test_get_l6_dataset_bad_dataset_type(dataset_urls_mock):
    # Test get L6 dataset with bad input dataset type
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_l6_dataset("Warra", "2024_v2", ds_type="bad-type")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get L6 dataset for site 'Warra', version '2024_v2': "
        "Requested 'bad-type' dataset is not found!"
    )


def test_get_datasets_from_multi_sites(dataset_urls_mock):
    datasets = flux.get_datasets(["AdelaideRiver", "WallabyCreek"], "2024_v2", "L3")
    assert set(datasets.keys()) == {"AdelaideRiver", "WallabyCreek"}
    assert {ds.attrs.get("site_name") for ds in datasets.values()} == {"Adelaide River", "Wallaby"}
    for ds in datasets.values():
        assert set(ds.variables) == {
            "AH",
            "CO2",
            "Flu",
            "AH_QCFlag",
            "CO2_QCFlag",
            "Flu_QCFlag",
            "time",
            "longitude",
            "latitude",
        }


def test_get_datasets_from_multiple_sites_bad_input(session_mock):
    # Bad site name
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_datasets(["bad-site-name", "AdelaideRiver"], "2024_v2", "L3")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get dataset for site 'bad-site-name', version '2024_v2', "
        "processing-level 'L3'"
    )


def test_get_subsets_from_multi_sites(dataset_urls_mock):
    # Test get_subsets with multiple datasets from different sites.
    subsets = flux.get_subsets(
        ["AdelaideRiver", "WallabyCreek"], "2024_v2", "L3", variables=["AH", "CO2"]
    )
    assert set(subsets.keys()) == {"AdelaideRiver", "WallabyCreek"}
    assert {ds.attrs.get("site_name") for ds in subsets.values()} == {"Adelaide River", "Wallaby"}
    for ds in subsets.values():
        assert set(ds.variables) == {
            "AH",
            "CO2",
            "AH_QCFlag",
            "CO2_QCFlag",
            "time",
            "longitude",
            "latitude",
        }


def test_get_subsets_from_multiple_sites_bad_input(session_mock):
    # Test get_subsets with multiple datasets from different sites, with bad version
    session_mock.return_value = mocked_response(status_code=404)
    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        flux.get_subsets(["Warra", "AdelaideRiver"], "bad-version", "L3")
    assert exc_info.typename == "Exception"
    assert str(exc_info.value).startswith(
        "Error: fail to get dataset for site 'Warra', version 'bad-version', "
        "processing-level 'L3'"
    )


def test_export_as_excel(dataset_urls_mock):
    # Test that excel file is generated
    with tempfile.TemporaryDirectory() as tmpdirname:
        outfile = os.path.join(tmpdirname, "test.xlsx")
        flux.export_as_excel(outfile, "AdelaideRiver", "2024_v2", "L3")
        assert os.path.exists(outfile)


def test_export_oneflux_csv(dataset_urls_mock):
    # Test that oneflux file is generated
    with tempfile.TemporaryDirectory() as tmpdirname:
        outdir = os.path.join(tmpdirname, "output")
        outfiles = flux.export_oneflux_csv(outdir, "WallabyCreek", "2024_v2", "L3")
        assert outfiles == [os.path.join(outdir, "Wallaby_qcv_2007.csv")]
        assert os.path.exists(outfiles[0])
