# This file contains export utilities to edxport dataset. These are adapted from
# https://github.com/OzFlux/PyFluxPro/tree/main/scripts.
import csv
import os

# from typing import Iterator
from collections.abc import Iterator
from datetime import datetime, timedelta

import numpy
import pytz
import xarray
import xlsxwriter

# oneflux variables configuration: name mapping and output format, and unit
# This is adapted from
# https://github.com/OzFlux/PyFluxPro/blob/main/controlfiles/standard/nc2csv_oneflux.txt.
# Note: the unit for VPD is hPa
ONEFLUX_VARIABLES_CFG = {
    "CO2": {"format": "{0:.3f}", "units": "umol/mol", "name": "CO2"},
    "Fco2": {"format": "{0:.4f}", "units": "umol/m^2/s", "name": "FC"},
    "Fg": {"format": "{0:d}", "units": "W/m^2", "name": "G"},
    "Fh": {"format": "{0:d}", "units": "W/m^2", "name": "H"},
    "H2O": {"format": "{0:.2f}", "units": "mmol/mol", "name": "H2O"},
    "Fe": {"format": "{0:d}", "units": "W/m^2", "name": "LE"},
    "Fld": {"format": "{0:d}", "units": "W/m^2", "name": "LW_IN"},
    "Flu": {"format": "{0:d}", "units": "W/m^2", "name": "LW_OUT"},
    "Fn": {"format": "{0:d}", "units": "W/m^2", "name": "NETRAD"},
    "Precip": {"format": "{0:.1f}", "units": "mm", "name": "P"},
    "ps": {"format": "{0:.1f}", "units": "kPa", "name": "PA"},
    "RH": {"format": "{0:d}", "units": "percent", "name": "RH"},
    "Sws": {"format": "{0:.3f}", "units": "m^3/m^3", "name": "SWC_1"},
    "Fsd": {"format": "{0:d}", "units": "W/m^2", "name": "SW_IN"},
    "Fsu": {"format": "{0:d}", "units": "W/m^2", "name": "SW_OUT"},
    "Ta": {"format": "{0:.2f}", "units": "degC", "name": "TA"},
    "Ts": {"format": "{0:.2f}", "units": "degC", "name": "TS_1"},
    "ustar": {"format": "{0:.2f}", "units": "m/s", "name": "USTAR"},
    "VPD": {"format": "{0:.3f}", "units": "hPa", "name": "VPD"},
    "Wd": {"format": "{0:d}", "units": "degrees", "name": "WD"},
    "Ws": {"format": "{0:.2f}", "units": "m/s", "name": "WS"},
}
# Missing value used in OzFlux datasets
FLUX_MISSING_VALUE = -9999


def npdt64_2datetime(dt: numpy.datetime64) -> datetime:
    """Convert from time in numpy.datetime64 to datetime object.

    Args:
        dt: Numpy datetime object.

    Returns:
        datetime object.
    """
    return dt.astype("M8[ms]").astype("O")


def perdelta(start: datetime, end: datetime, delta: timedelta) -> Iterator[datetime]:
    """Yields iterator of datetime objects from start to end with time step delta.

    Args:
        start: Start time.
        end: End time.
        delta: Time step.

    Yields:
        iterator of datetime objects
    """
    curr = start
    while curr <= end:
        yield curr
        curr += delta


def get_fluxnet_id(ds: xarray.Dataset) -> str:
    """Get fluxnet ID for the site the dataset is in.

    Args:
        ds: xarray Dataset.

    Returns:
        Fluxnet ID.
    """
    fluxnet_id = ds.attrs.get("fluxnet_id")
    if fluxnet_id and len(fluxnet_id) == 6:
        return fluxnet_id
    return ds.attrs.get("site_name", "")


def strip_non_numeric(s1: str) -> str:
    """Strip non-numeric characters from a string.

    Args:
        s1: A string.

    Returns:
        A string with digits only.
    """
    return "".join([c for c in s1 if c in "-1234567890."])


def FindMatchingIndices(a: numpy.array, b: numpy.array) -> tuple[list[str], list[str]]:
    """Find the indices of elements in array a that match elements in array b and vice versa.

    Args:
        a: First array.
        b: Second array.

    Returns:
        A tuple of:
        inds_a - the indices of elements in a that match elements in b
        inds_b - the indices of elements in b that match elements in a

    """
    a1 = numpy.argsort(a)
    b1 = numpy.argsort(b)
    # use searchsorted:
    sort_left_a = a[a1].searchsorted(b[b1], side="left")
    sort_right_a = a[a1].searchsorted(b[b1], side="right")
    sort_left_b = b[b1].searchsorted(a[a1], side="left")
    sort_right_b = b[b1].searchsorted(a[a1], side="right")
    # which values of b are also in a?
    inds_b = (sort_right_a - sort_left_a > 0).nonzero()[0]
    # which values of a are also in b?
    inds_a = (sort_right_b - sort_left_b > 0).nonzero()[0]
    return inds_a, inds_b


def xlsx_add_attrsheet(ds: xarray.Dataset, xlworkbook: xlsxwriter.Workbook) -> None:
    """Add an excel sheet with dataset's global attributes and variables' attributes.

    Args:
        ds: Dataset
        xlworkbook: Excel workbook object
    """
    # Add a sheet to the excel file
    xlSheet = xlworkbook.add_worksheet("Attr")
    # write the global attributes
    xlSheet.write(0, 0, "Global attributes")
    xlrow = 1  # noqa: SIM113
    for k, v in sorted(ds.attrs.items()):
        xlSheet.write(xlrow, 0, k)
        xlSheet.write(xlrow, 1, str(v))
        xlrow += 1

    # write the variable attributes
    xlrow += 1
    xlSheet.write(xlrow, 0, "Variable attributes")
    xlrow += 1
    variables = sorted(ds.keys())
    for var in ["crs", "station_name"]:
        if var in variables:
            variables.remove(var)

    for var in variables:
        xlSheet.write(xlrow, 0, var)  # write variable name on 1st column
        for k, v in sorted(ds.variables[var].attrs.items()):
            xlSheet.write(xlrow, 1, k)  # attribute name on 2nd column
            xlSheet.write(xlrow, 2, str(v))  # attribute value on 3rd column
            xlrow = xlrow + 1


def xlsx_add_datasheet(ds: xarray.Dataset, xlworkbook: xlsxwriter.Workbook) -> None:
    """Add an excel sheet with dataset variable data.

    Args:
        ds: Dataset
        xlworkbook: Excel workbook object
    """
    # Add a sheet to the excel file
    xlSheet = xlworkbook.add_worksheet("Data")

    column_header_row = 2  # Row 2 for variable names as column
    value_start_row = 3  # Row 3 for values

    # Column 0: time
    dt_format = xlworkbook.add_format({"num_format": "dd/mm/yyyy hh:mm"})

    xlSheet.write(column_header_row, 0, "xlDateTime")  # row 2: column name
    nRecs = ds.time.shape[0]
    times = [npdt64_2datetime(t) for t in ds.variables["time"].data]
    # write time values, starting from row 1
    for i in range(nRecs):
        xlSheet.write_datetime(value_start_row + i, 0, times[i], dt_format)

    # Get the variables, excluding the QCFlag variables
    variables = list(ds.keys())
    for var in ["crs", "station_name"]:
        if var in variables:
            variables.remove(var)
    variables = sorted([v for v in variables if "QCFlag" not in v])

    xlcol = 1  # noqa: SIM113
    for vname in variables:
        # Row 0: variable long name
        # Row 1: variable units
        # Row 2: variable name
        longname = ds.variables[vname].attrs.get("long_name") or ds.variables[vname].attrs.get(
            "Description"
        )
        units = ds.variables[vname].attrs.get("units") or ds.variables[vname].attrs.get("Units")
        xlSheet.write(0, xlcol, longname)
        xlSheet.write(1, xlcol, units)
        xlSheet.write(column_header_row, xlcol, vname)

        # write values to excel sheet
        for i in range(nRecs):
            xlSheet.write(value_start_row + i, xlcol, float(ds.variables[vname].data[i][0][0]))
        # Next column
        xlcol += 1


def xlsx_add_flagsheet(ds: xarray.Dataset, xlworkbook: xlsxwriter.Workbook) -> None:
    """Add an excel sheet with dataset variable flag data.

    Args:
        ds: Dataset
        xlworkbook: Excel workbook object
    """
    # Add a sheet to the excel file
    xlSheet = xlworkbook.add_worksheet("Flag")

    # Column 0: time
    dt_format = xlworkbook.add_format({"num_format": "dd/mm/yyyy hh:mm"})

    xlSheet.write(0, 0, "xlDateTime")  # row 0: column name
    nRecs = ds.time.shape[0]
    times = [npdt64_2datetime(t) for t in ds.variables["time"].data]
    # write time values, starting from row 1
    for i in range(nRecs):
        xlSheet.write_datetime(i + 1, 0, times[i], dt_format)

    # write the variable QC flags
    variables = list(ds.keys())
    for var in ["crs", "station_name"]:
        if var in variables:
            variables.remove(var)
    # Assume there is a qc flag variable for each variable
    qc_variables = [v for v in variables if "QCFlag" in v]
    variables = sorted([v for v in variables if "QCFlag" not in v])

    xlcol = 1
    for vname in variables:
        # write the associated QC flag variable
        if vname + "_QCFlag" in qc_variables:
            xlSheet.write(0, xlcol, vname)  # Write variable name
            # specify the format of the QC flag (integer)
            flag_format = xlworkbook.add_format({"num_format": "0"})
            # write QC flag values to excel sheet
            for i in range(nRecs):
                xlSheet.write(
                    i + 1, xlcol, int(ds.variables[vname + "_QCFlag"].data[i][0][0]), flag_format
                )
            # Next column
            xlcol += 1


def xlsx_write_dataset(ds: xarray.Dataset, xlfilename: str) -> None:
    """Export the dataset as Excel workbook.

    Args:
        ds: The dataset.
        xlfilename: Excel output file.
    """
    # open the Excel file
    with xlsxwriter.Workbook(xlfilename, {"date_1904": False, "nan_inf_to_errors": True}) as xlfile:
        # Add the attribute, data and QC flag sheets to Excel workbook
        xlsx_add_attrsheet(ds, xlfile)
        xlsx_add_datasheet(ds, xlfile)
        xlsx_add_flagsheet(ds, xlfile)


def write_csv_oneflux(ds: xarray.Dataset, outdir: str) -> list[str]:
    """Export the dataset specified in oneFlux csv format.

    The generated csv files are in the specified output folder.

    Args:
        ds: Dataset.
        outdir: Output folder.

    Returns:
        A list of output oneflux csv files.
    """
    ts_delta = timedelta(minutes=int(ds.attrs["time_step"]))
    start_year = (npdt64_2datetime(ds.coords["time"].data[0]) - ts_delta).year
    end_year = (npdt64_2datetime(ds.coords["time"].data[-1]) - ts_delta).year
    years = range(start_year, end_year + 1)
    output_files = []
    for year in years:
        output_files.append(write_csv_oneflux_year(ds, year, outdir))
    return output_files


def write_csv_oneflux_year(ds: xarray.Dataset, year: int, outdir: str) -> str:
    """Export the dataset for the specified year in oneflux format.

    The generated csv files are in the specified output folder.

    Args:
        ds: Dataset.
        year: Year of the data.
        outdir: Output folder.

    Returns:
        Output oneflux csv file.
    """
    # Keep only variables needed for fluxone
    variables = [v for v in ONEFLUX_VARIABLES_CFG if v in ds.variables]
    ds = ds[variables]
    time_resolution = {30: "halfhourly", 60: "hourly"}
    ts_delta = timedelta(minutes=int(ds.attrs["time_step"]))

    # datetime array from start to end at ts
    start = datetime(year, 1, 1, 0, 0, 0) + ts_delta  # noqa: DTZ001
    end = datetime(year + 1, 1, 1, 0, 0, 0)  # noqa: DTZ001
    cdt = numpy.array(list(perdelta(start, end, ts_delta)))
    nrecs = len(cdt)

    # Find the indexes (i.e. intersection of full year time-axis and variable time-axis)
    var_dt = numpy.array([npdt64_2datetime(t) for t in ds.coords["time"].data])
    a1, b1 = FindMatchingIndices(cdt, var_dt)

    # Variable data
    data = {"DateTime": {"data": cdt}}
    # ONEFlux variable labels
    # variables = [k for k in ds.keys() if k not in ("crs", "station_name")]
    for var in variables:
        data[var] = {}
        # prefill data with non-exist value
        data[var]["data"] = numpy.full(nrecs, float(FLUX_MISSING_VALUE))

        # Copy the variable data for the year
        if var == "VPD":
            # For VPD, do unit conversion from Kpa to hpa
            data[var]["data"][a1] = numpy.array([i[0][0]/10.0 for i in ds.variables[var].data[b1]])
        else:
            data[var]["data"][a1] = numpy.array([i[0][0] for i in ds.variables[var].data[b1]])

    # get the UTC offset from the time zone name
    now = datetime.now(pytz.timezone(ds.attrs["time_zone"]))
    utc_offset = now.utcoffset().total_seconds() / 60 / 60
    # get the tower height
    tower_height = strip_non_numeric(str(ds.attrs["tower_height"]))

    # get the data path and CSV name
    fluxnet_id = get_fluxnet_id(ds)
    csv_filepath = os.path.join(outdir, f"{fluxnet_id}_qcv_{year}.csv")
    # open the csv file for output
    with open(csv_filepath, "w") as csv_file:
        writer = csv.writer(csv_file)
        # write the header lines
        writer.writerow(["site", fluxnet_id])
        writer.writerow(["year", str(year)])
        writer.writerow(["lat", str(ds.attrs["latitude"])])
        writer.writerow(["lon", str(ds.attrs["longitude"])])
        writer.writerow(["timezone", str(utc_offset)])
        writer.writerow(["htower", "{:%Y%m%d%H%M}".format(start), str(tower_height)])
        writer.writerow(["timeres", time_resolution[int(ds.attrs["time_step"])]])
        writer.writerow(["sc_negl", str(1)])
        writer.writerow(["notes", "Adapted from PyFluxPro"])
        # write the data
        header = ["TIMESTAMP_START", "TIMESTAMP_END"]
        for var in variables:
            # Rename variables from the configuration
            header.append(ONEFLUX_VARIABLES_CFG[var]["name"])
        writer.writerow(header)

        # Write per row, start/end times, variables' values
        for n in range(nrecs):
            dtime = cdt[n]
            time_start = "{:%Y%m%d%H%M}".format(dtime - ts_delta)
            time_end = "{:%Y%m%d%H%M}".format(dtime)
            data_list = [time_start, time_end]
            for var in variables:
                strfmt = ONEFLUX_VARIABLES_CFG[var]["format"]
                value = data[var]["data"][n]
                if "d" in strfmt:
                    data_list.append(strfmt.format(int(round(value))))
                else:
                    data_list.append(strfmt.format(value))
            writer.writerow(data_list)
    return csv_filepath
