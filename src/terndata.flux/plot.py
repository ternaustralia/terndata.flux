import datetime

import matplotlib.dates as mdt
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from mpl_toolkits.axes_grid1 import make_axes_locatable


def npdt64_to_datetime(dt64_times: np.ndarray) -> np.ndarray:
    """Convert numpy datetime64 to datetime time series.

    Args:
        dt64_times: time-series data in numpy datetime64 format (1 second).

    Returns:
        time series data in datetime format.
    """
    # Compute the number of seconds since epoch time, then convert to datetime
    epoch = "1970-01-01T00:00:00"
    xts = (dt64_times - np.datetime64(epoch)) / np.timedelta64(1, "s")
    return np.array([datetime.datetime.fromtimestamp(dt) for dt in xts])  # noqa: DTZ006


def plot_timeseries(xds: xr.Dataset, varnames: str | list[str]):
    """Generate time-series plot for the dataset's variables specified.

    Adapted from PyFluxPro (https://github.com/OzFlux/PyFluxPro).

    Args:
        xds: An xarray dataset.
        varnames: List of variable names to be plotted.

    Raises:
        Exception: An exception for invalid parameter varnames.
    """
    site_name = xds.attrs.get("site_name", "")
    if isinstance(varnames, str):
        varnames = [varnames]
    elif not isinstance(varnames, list):
        raise Exception("Argument 'varnames' must be a string or a list")

    nrows = len(varnames)
    fig, axs = plt.subplots(nrows=nrows, sharex=True, figsize=(10.9, 7.5))
    fig.subplots_adjust(wspace=0.0, hspace=0.05, left=0.1, right=0.95, top=0.95, bottom=0.1)
    if nrows == 1:
        axs = [axs]
    fig.canvas.manager.set_window_title(site_name)
    for n, var in enumerate(varnames):
        xdt = xds["time"].values.astype("datetime64[s]")
        data = xds[var].data[:, 0, 0]
        dt_data = npdt64_to_datetime(xdt)

        # count of valid data
        data_count = data.size - np.isnan(data).sum()
        count_str = f"Total {data.size}, Usable {data_count} ({np.rint(100*data_count/data.size)}%)"
        start = dt_data[0]
        end = dt_data[-1]
        axs[n].plot(dt_data, data, "b.", label=f"{var} {count_str}")
        axs[n].legend()
        axs[n].set_xlim([start, end])
        if n == 0:
            title = f"{site_name}: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            axs[n].set_title(title)
        if n == nrows - 1:
            axs[n].set_xlabel("Date")
        axs[n].set_ylabel(f"({xds[var].attrs.get('units', '')})")
    plt.show()


def plot_fingerprints(xds: xr.Dataset, varnames: str | list[str]):
    """Generate finger-prints plot for the dataset's variable specified.

    Adapted from PyFluxPro (https://github.com/OzFlux/PyFluxPro).

    Args:
        xds: An xarray dataset.
        varnames: List of variable names to be plotted.

    Raises:
        Exception: An exception for invalid parameter varnames.
    """
    site_name = xds.attrs.get("site_name", "")
    ts = int(float(xds.attrs["time_step"]))
    if isinstance(varnames, str):
        varnames = [varnames]
    elif not isinstance(varnames, list):
        raise Exception("Argument 'varnames' must be a string or a list")

    # create the figure
    ncols = len(varnames)
    fig, axs = plt.subplots(ncols=ncols, sharey=True, figsize=(7.5, 10.9))
    # axs must be a list
    if ncols == 1:
        axs = [axs]
    fig.subplots_adjust(wspace=0.05, hspace=0.05, left=0.1, right=0.95, top=0.95, bottom=0.1)
    # put a title on the figure window
    fig.canvas.manager.set_window_title(site_name)

    # get the start and end dates for whole days
    ts = int(float(xds.attrs["time_step"]))
    time_data = xds["time"]
    td = np.timedelta64(1, "D") + np.timedelta64(ts, "m")
    start = time_data[0].astype("datetime64[D]") + td
    td = +np.timedelta64(0, "m")
    end = time_data[-1].astype("datetime64[D]") + td
    ldt = xds["time"].sel(time=slice(start, end)).values[:]

    # put a title on the figure
    title = f"{site_name}: {np.datetime_as_string(start, 'D')} to {np.datetime_as_string(end, 'D')}"
    fig.suptitle(title, fontsize=16)

    # get the number of records per day and the number of whole days
    nPerHr = int(float(60) / ts + 0.5)
    nPerDay = int(float(24) * nPerHr + 0.5)
    nDays = len(ldt) // nPerDay

    # loop over variables to be plotted
    for n, var in enumerate(varnames):
        # get the variable data
        data = xds[var].sel(time=slice(start, end)).values[:, 0, 0]
        if data.size - np.isnan(data).sum() == 0:
            # print(f"{var}: no data found, skipping...")
            continue
        # reshape into a 2D array
        data_daily = data.reshape(nDays, nPerDay)
        # clip data to the 0.25 and 99.75 percentiles to suppress outliers
        # this helps make the colour scale even
        vmin = np.nanpercentile(data_daily, 0.25)
        vmax = np.nanpercentile(data_daily, 99.75)
        # get the start and end dates as numbers
        sd = mdt.date2num(start)
        ed = mdt.date2num(end)
        # render the image
        im = axs[n].imshow(
            data_daily,
            extent=[0, 24, sd, ed],
            aspect="auto",
            origin="lower",
            interpolation="none",
            cmap="viridis",
            vmin=vmin,
            vmax=vmax,
        )
        # add a colour bar
        divider = make_axes_locatable(axs[n])
        cax = divider.append_axes("bottom", size="1%", pad=0.5)
        fig.colorbar(im, cax=cax, orientation="horizontal")
        # do the major ticks on the Y (date) axis
        axs[n].yaxis_date()
        axs[n].yaxis.set_major_locator(mdt.YearLocator())
        axs[n].yaxis.set_major_formatter(mdt.DateFormatter("%Y"))
        # set the ticks on the X (hour) axis
        axs[n].set_xticks([0, 6, 12, 18, 24])
        # label the X axis
        xlabel = f"{var} ({xds[var].attrs.get('units', '')})"
        axs[n].set_xlabel(xlabel)
        # suppress the Y axis labels if more than 1 image
        if n != 0:
            plt.setp(axs[n].get_yticklabels(), visible=False)
    # render the fingerprint
    plt.show()
