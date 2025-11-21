"""TERN flux data API methods.

This module provides API methods for accessing TERN flux data.
"""

import os
from datetime import datetime
from multiprocessing import Pool, set_start_method

import geopandas as gpd
import pandas as pd
import xarray as xr

from .export_utils import FLUX_MISSING_VALUE, write_csv_oneflux, xlsx_write_dataset
from .utils import (
    DEFAULT_DATASET,
    get_catalog_items,
    get_catalog_url,
    get_dataset_urls,
    is_isoformat,
)


def get_versions(site: str) -> list[str]:
    """Get the versions available for the specified site.

    Args:
        site: Site name

    Returns:
        A list of versions available for the specified site.

    Raises:
        Exception: Exception for fail to get versions.
    """
    # version catalog access url for the site.
    try:
        cat_url = get_catalog_url("version", params={"site": site})
        return list(get_catalog_items(cat_url).keys())
    except Exception as e:
        raise Exception(
            f"Error: fail to get versions for site '{site}': {str(e)}"
        ) from e  # noqa: DAR401


def get_processing_levels(site: str, version: str) -> list[str]:
    """Get the processing-levels available for the specified site and version.

    Args:
        site: Site name.
        version: Dataset version.

    Returns:
        A list of processing-levels available for the specified site and version.

    Raises:
        Exception: Exception for fail to get processing-levels.
    """
    # Proccessing-level catalog access url.
    try:
        cat_url = get_catalog_url("processing_level", params={"site": site, "version": version})
        return list(get_catalog_items(cat_url).keys())
    except Exception as e:
        raise Exception(
            f"Error: fail to get processing-levels for site '{site}', version '{version}': {str(e)}"
        ) from e  # noqa: DAR401


def _get_dataset(url: str, missing_as_nan: bool = False) -> xr.Dataset:
    # Return the specified dataset as xarray Dataset.
    dataset = xr.open_dataset(url, engine="netcdf4")
    if missing_as_nan:
        # set missing value for each variables
        for var in dataset.variables:
            if var in dataset.coords:
                # skip coordinate variables
                continue
            dataset.variables[var].attrs["missing_value"] = FLUX_MISSING_VALUE
        dataset = xr.decode_cf(dataset)
    return dataset


def get_dataset(
    site: str, version: str, processing_level: str = "L3", missing_as_nan: bool = False
) -> xr.Dataset:
    """Get the 30-min (default) dataset for the specified site, version and processing-level.

    Args:
        site: Site name.
        version: Dataset version.
        processing_level: Dataset processing-level. Defaults to "L3"
        missing_as_nan: Whether to set the missing value as nan in the dataset. Defaults to False.

    Returns:
        An xarray dataset for the site, version and processing-level specified.

    Raises:
        Exception: Exception for fail to get dataset.
    """
    # Fetch the dataset access URLs
    try:
        dataset_urls = get_dataset_urls(site, version, processing_level)
        return _get_dataset(dataset_urls[DEFAULT_DATASET], missing_as_nan)
    except Exception as e:
        raise Exception(
            f"Error: fail to get dataset for site '{site}', version '{version}', "
            f"processing-level '{processing_level}': {str(e)}"
        ) from e  # noqa: DAR401


def get_global_attributes(
    site: str,
    version: None | str = None,
    processing_level: str = "L3",
) -> dict:
    """Get the global attributes of the 30min dataset specified.

    Args:
        site: Site name.
        version: Dataset version. Defaults to None.
        processing_level: Dataset processing-level. Defaults to "L3".

    Returns:
        A dictionary of the dataset's attributes.
    """
    if version is None:
        # Get the latest version.
        version = max(get_versions(site))
    return get_dataset(site, version, processing_level).attrs


def get_variables(site: str, version: None | str = None, processing_level: str = "L3") -> list[str]:
    """Get the names of the variables for the 30min dataset specified.

    Args:
        site: Site name.
        version: Dataset version. Defaults to None.
        processing_level: Dataset processing-level. Defaults to "L3".

    Returns:
        A list of dataset's variable names
    """
    if version is None:
        # Get the latest version.
        version = max(get_versions(site))
    # TODO: Exclude coordinate variables, crs and station_name????
    # exclude_vars = list(dataset.variables.keys()) + ["crs", "station_name"]
    # return [var for var in dataset.variables if var not in exclude_vars]
    return list(get_dataset(site, version, processing_level).variables.keys())


def get_attributes(
    site: str,
    version: None | str = None,
    processing_level: str = "L3",
    variables: None | list[str] = None,
) -> dict:
    """Get the attributes for the 30min dataset's variables specified.

    Args:
        site: Site name.
        version: Dataset version. Defaults to None.
        processing_level: Dataset processing-level. Defaults to "L3".
        variables: List of variables

    Returns:
        A dictionary of the dataset's attributes.

    Raises:
        ValueError: An exception for invalid variables specified.
    """
    if version is None:
        # Get the latest version.
        version = max(get_versions(site))
    dataset = get_dataset(site, version, processing_level)
    if variables is None:
        variables = list(dataset.variables.keys())
    else:
        # check that attributes are valid
        if {var in dataset.variables for var in variables} != {True}:
            raise ValueError(f"{variables} has invalid variable")

    # return the variables' attributes
    return {var: dataset.variables[var].attrs for var in variables}


def _get_location(site: str) -> dict:
    """Get location coordinates for the site.

    Args:
        site: Site name.

    Returns:
        A dictionary with site name and coordinates,
    """
    # Based on the latest version, L6, 30-min dataset.
    latest_version = max(get_versions(site))

    # Some sites (i.e. DryRiver) may not have L6 30-min netcdf files.
    # Get from one of the processing levels available
    for plevel in ["L6", "L5", "L4", "L3"]:
        try:
            dataset = get_dataset(site, latest_version, plevel)
            if dataset:
                break
        except Exception as e:
            continue
    return {
        "site": site,
        "longitude": float(dataset.coords["longitude"].data[0]),
        "latitude": float(dataset.coords["latitude"].data[0]),
        "vegetation": dataset.attrs.get("vegetation"),
        "canopy height": dataset.attrs.get("canopy_height"),
        "start": dataset.attrs.get("time_coverage_start"),
        "end": dataset.attrs.get("time_coverage_end"),
    }


def get_sites() -> gpd.GeoDataFrame:
    """List all the sites and their locations.

    The location is based on the latest version, L6 of 30-min/default dataset.

    Returns:
        A GeoDataFrame containing a list of site location with site name, longitude and latitude.

    Raises:
        Exception: An exception for fail to get sites.
    """
    # Get site names
    try:
        cat_url = get_catalog_url("site")
        sites = get_catalog_items(cat_url).keys()
    except Exception as e:
        raise Exception(f"Error: fail to get sites: {str(e)}") from e  # noqa: DAR401

    # Get locations
    # Use spawn worker process to avoid issue with requests.Session not being thread safe.
    # TODO: Shall use thread instead of multiprocessor. https://realpython.com/python-concurrency
    set_start_method("spawn", force=True)
    with Pool(processes=6) as pool:
        locations = pool.map(_get_location, sites)
    # convert into GeoDataFrame
    df = pd.DataFrame.from_dict(locations)
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))


def get_temporal_range(site: str, version: str, processing_level: str = "L3") -> tuple[str, str]:
    """Get the temporal range for 30min dataset of the site, version, processing-level specified.

    Args:
        site: Site name.
        version: Dataset version.
        processing_level: Dataset processing-level. Defaults to "L3".

    Returns:
        A tuple of date and time, indicating the start and end timestamps.
    """
    # 30min dataset access URL.
    dataset = get_dataset(site, version, processing_level)
    return (str(dataset.coords["time"].data[0]), str(dataset.coords["time"].data[-1]))


def get_coordinates(site: str, version: str, processing_level: str = "L3") -> list[str]:
    """Get dataset's coordinate variables for the site, version, processing-level specified.

    Args:
        site: Site name.
        version: Dataset version.
        processing_level: Dataset processing-level. Defaults to "L3".

    Returns:
        A list of dataset's coordinate variable names.
    """
    dataset = get_dataset(site, version, processing_level)
    return list(dataset.coords.keys())


def get_l6_dataset(
    site: str, version: str, ds_type: str, missing_as_nan: bool = False
) -> xr.Dataset:
    """Get the L6-dataset of the specified dataset type for the site specified.

    Args:
        site: Site name.
        version: Dataset version.
        ds_type: Dataset type: 30min, hourly, daily, monthly, annual, cumulative.
        missing_as_nan: Whether to set the missing value as nan in the dataset. Defaults to False.

    Returns:
        A xarray dataset.

    Raises:
        Exception: An exception for fail to get L6 dataset.
    """
    # Dataset access URL.
    try:
        dataset_urls = get_dataset_urls(site, version, "L6")
        if ds_type not in dataset_urls:
            raise Exception(f"Requested '{ds_type}' dataset is not found!")
        return _get_dataset(dataset_urls[ds_type], missing_as_nan)
    except Exception as e:
        raise Exception(
            f"Error: fail to get L6 dataset for site '{site}', version '{version}': {str(e)}"
        ) from e  # noqa: DAR401


def get_datasets(
    sites: list[str],
    version: str,
    processing_level: str = "L3",
    missing_as_nan: bool = False,
) -> dict[str, xr.Dataset]:
    """Get the 30min/default datasets for the specified sites, version, processing-level.

    Args:
        sites: A list of site names.
        version: Dataset version.
        processing_level: Dataset processing-level. Defaults to "L3".
        missing_as_nan: Whether to set the missing value as nan in the dataset. Defaults to False.

    Returns:
        A dictionary of datasets for the specified sites, version and processing level,
        indexed by site name.
    """
    datasets = {}
    for site in sites:
        datasets[site] = get_dataset(site, version, processing_level, missing_as_nan)
        # TODO: Cannot load the dataset for some reasons i.e. dataset does not exists.
        # This can be due to wrong input parameters (i.e. 2024_v3 instead of 2024_v2),
        # or some sites do not have the version specified (i.e. AliceMulga only has 2025_v1)
        # What shall we do? silently ignore it??
        # datasets[site][version] = None
    return datasets


def get_subset(
    site: str,
    version: None | str = None,
    processing_level: str = "L3",
    variables: None | list[str] = None,
    start: None | str | datetime = None,
    end: None | str = None,
    keep_attrs: bool = True,
    keep_qcflags: bool = True,
    missing_as_nan: bool = False,
) -> xr.Dataset:
    """Get a subset of dataset containing only the specified variables, and time range.

    If variables is not specified, then all variables are included. If start/end time are not
    specified, then full time series of data is included. By default, corresponding variables' qc
    flags are included. The start/end time can be in ISO-formatted string (i.e. yyyy-mm-dd HH:MM).

    Args:
        site: Site name.
        version: Dataset version. Default to None.
        processing_level: Dataset processing-level. Default to "L3"
        variables: Dataset variable names. Defaults to None.
        start: Data start time, an ISO-formatted string or datetime object. Defaults to None.
        end: Data end time, an ISO-formatted string or datetime object. Defaults to None.
        keep_attrs: Whether to keep variable attributes. Defaults to True.
        keep_qcflags: Whether to keep the corresponding variables' QC flags. Defaults to True.
        missing_as_nan: Whether to set the missing value as nan in the dataset. Defaults to False.

    Returns:
        A xarray dataset with the variables specified.

    Raises:
        Exception: An exception for fail to get subset.
        ValueError: An exception for invalid ISO-formatted date parameter.
    """
    if version is None:
        # Get the latest version.
        version = max(get_versions(site))

    dataset = get_dataset(site, version, processing_level, missing_as_nan)
    if variables:
        # check if variables specified are valid
        for var in variables:
            if var not in dataset.variables:
                raise Exception(
                    f"Error: fail to get subset for site '{site}': variable '{var}' not found"
                )  # noqa: DAR401
        qcFlags = []
        if keep_qcflags:
            # Add the corresponding QC flags if they exist
            for var in variables:
                if "_QCFlag" in var:
                    # skip qc flag variable
                    continue
                qcFlag = f"{var}_QCFlag"
                if qcFlag in dataset.variables:
                    qcFlags.append(qcFlag)
        dataset = dataset[variables + qcFlags]

    # Check for time slicing request
    if start or end:
        # Time slicing the dataset
        if start is None:
            start = str(dataset.coords["time"].data[0])[:19]  # Trucate to yyyy-mm-ddTHH:MM:SS
        elif isinstance(start, str) and not is_isoformat(start):
            raise ValueError(f"Invalid ISO-format start time {start}")
        if end is None:
            end = str(dataset.coords["time"].data[-1])[:19]  # Trucate to yyyy-mm-ddTHH:MM:SS
        elif isinstance(end, str) and not is_isoformat(end):
            raise ValueError(f"Invalid ISO-format end time {end}")
        # slice along the temporal range
        dataset = dataset.sel(time=slice(start, end))

    # Finally, check if variable attributes are to be cleared
    if not keep_attrs:
        for var in dataset.variables:
            dataset.variables[var].attrs = {}
    return dataset


def get_subsets(
    sites: list[str],
    version: None | str = None,
    processing_level: str = "L3",
    variables: None | list[str] = None,
    start: None | str = None,
    end: None | str = None,
    keep_attrs: bool = True,
    keep_qcflags: bool = True,
    missing_as_nan: bool = False,
) -> dict[str, xr.Dataset]:
    """Get subset of 30min datasets for the specified variables and time range from specified sites.

    If variables is not specified, then all variables are included. If start/end time are not
    specified, then full time series of data is included.
    The start/end time can be in ISO-formatted string (i.e. yyyy-mm-dd HH:MM).

    Args:
        sites: List of site names.
        version: Dataset version. Default to from datetime import datetimeNone.
        processing_level: Dataset processing-level. Default to "L3"
        variables: Dataset variable names. Defaults to None.
        start: Data start time, an ISO-formatted string or datetime object. Defaults to None.
        end: Data end time, an ISO-formatted string or datetime object. Defaults to None.
        keep_attrs: Whether to keep variable attributes. Defaults to True.
        keep_qcflags: Whether to keep the corresponding variables' QC flags. Defaults to True.
        missing_as_nan: Whether to set the missing value as nan in the dataset. Defaults to False.

    Returns:
        A dictionary of xarray datasets, indexed by site name.
    """
    return {
        site: get_subset(
            site,
            version,
            processing_level,
            variables,
            start,
            end,
            keep_attrs,
            keep_qcflags,
            missing_as_nan,
        )
        for site in sites
    }


def export_as_excel(
    filename: str,
    site: str,
    version: str | None = None,
    processing_level: str = "L6",
) -> None:
    """Export the 30min/default dataset of the specified site, version and processing-level in excel format.

    The method exports the dataset in excel format to the file specified

    Args:
        filename: Output excel file (must have 'xlxs' as extension).
        site: Site name.
        version: Dataset version. Defaults to None, indicating latest versions.
        processing_level: dataset processing-level. Defaults to "L6".

    Returns:
        A Excel workbook file path.

    Raises:
        Exception: An exception for fail to export dataset.
    """
    # export the 30-min dataset from specified site, version and processing-level in csv format
    # to file specified.
    if not filename.endswith(".xlsx"):
        raise Exception(f"Filename {filename} has invalid excel extension: must end with '.xlsx'.")
    if version is None:
        version = max(get_versions(site))

    # Generate output in excel format
    try:
        ds = get_dataset(site, version, processing_level)
        xlsx_write_dataset(ds, filename)
        return filename
    except Exception as e:
        raise Exception(f"Export dataset as Excel Workbook failed: {str(e)}") from e  # noqa: DAR401


def export_oneflux_csv(
    outdir: str,
    site: str,
    version: str | None = None,
    processing_level: str = "L4",
) -> list[str]:
    """Export the 30min/default dataset of specified site, version and processing-level in oneFlux csv format.

    The method exports the dataset in oneFlux csv format to the output folder specified.
    Note that there is no unit conversion i.e. unit for VPD remains as Kpa.

    Args:
        outdir: Output folder for the generated csv files.
        site: Site name.
        version: Dataset version. Defaults to None, indicating latest versions.
        processing_level: dataset processing-level. Defaults to "L4".

    Returns:
        A list of output oneflux csv files.

    Raises:
        Exception: An exception for fail to export dataset.
    """
    try:
        # oneflux is only avaliable for L3 and L4.
        if processing_level not in ["L3", "L4"]:
            raise Exception(
                f"Invalid processing level {processing_level}: only available for L3 or L4."
            )

        # export the 30-min dataset from specified site, version and processing-level in OneFlux csv format
        # to file specified.
        # Ensure output folder exists
        os.makedirs(outdir, exist_ok=True)
        if version is None:
            version = max(get_versions(site))

        # Export dataset in oneFlux csv format
        ds = get_dataset(site, version, processing_level)
        return write_csv_oneflux(ds, outdir)
    except Exception as e:
        raise Exception(f"Export dataset in oneflux format failed: {str(e)}") from e  # noqa: DAR401
