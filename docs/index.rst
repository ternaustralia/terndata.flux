.. rst-class:: hide-header

Welcome to tern_data_package
============================

This package aims to provide some API methods to access and work with TERN flux datasets, that are
availble from `TERN THREDDS server <https://dap.tern.org.au/>`_.


Installation
-------------

Build the package wheel and install locally:

.. code-block:: bash

    python -m build
    pip install <tern_data_package-xxx.whl>


Or install from repository:

.. code-block:: bash

    pip install git+hhttps://bitbucket.org/terndatateam/tern-data-package@<version>


Getting started
---------------

See the following examples to help you get started, with sample output (indicated by >>>) where appropriate. Refer to API documentation for details.

.. code-block:: python3

    from tern_data_package import flux_api

    # Get sites where flux data is available
    sites = flux_api.get_sites()
    >>>                                  site   longitude   latitude                     geometry
        0                       AdelaideRiver  131.117800 -13.076900    POINT (131.1178 -13.0769)
        1                   AliceSpringsMulga  133.249000 -22.283000      POINT (133.249 -22.283)
        2                      AlpinePeatland  147.320833 -36.862222  POINT (147.32083 -36.86222)
        3                             Boyagin  116.938559 -32.477093  POINT (116.93856 -32.47709)
        4                    CalperumChowilla  140.587700 -34.002700    POINT (140.5877 -34.0027)
        5                     CapeTribulation  145.446922 -16.103219  POINT (145.44692 -16.10322)
        6                              Collie  116.237000 -33.420000       POINT (116.237 -33.42)
        7                              CowBay  145.427150 -16.238189  POINT (145.42715 -16.23819)
        8                     CumberlandPlain  150.723611 -33.615278  POINT (150.72361 -33.61528)
        9                         DalyPasture  131.318100 -14.063300    POINT (131.3181 -14.0633)
        ...
    
    # get the versions available for the site
    versions = flux_api.get_versions("AdelaideRiver")
    >>> ['2020', '2021_v1', '2022_v1', '2022_v2', '2023_v1', '2023_v2', '2024_v1', '2024_v2']

    # Get the processing-levels available for a site and version
    processing_levels = flux_api.get_processing_levels("AdelaideRiver", "2024_v2")
    >>> ['L3', 'L4', 'L5', 'L6']

    # Get a 30min dataset from a site, and of a version and processing-level.
    30min_ds = flux_api.get_dataset("AdelaideRiver", "2024_v2", "L3")
    >>> <xarray.Dataset> Size: 18MB
    Dimensions:             (time: 28070, latitude: 1, longitude: 1)
    Coordinates:
    * time                (time) datetime64[ns] 225kB 2007-10-17T11:30:00 ... 2...
    * latitude            (latitude) float64 8B -13.08
    * longitude           (longitude) float64 8B 131.1
    ...

    # Get a daily dataset
    daily_ds = get_l6_daily("AdelaideRiver", "2024_v2")

    # Get a yearly dataset
    daily_ds = flux_api.get_l6_annual("AdelaideRiver", "2023_v1")

    # Get 30min datasets from multiple sites
    sites = ["AdelaideRiver", "Warra"]
    datasets = flux_api.get_datasets(sites, "2024_v2", "L6")
    >>> {'AdelaideRiver': <xarray.Dataset> Size: 24MB
    Dimensions:             (time: 28070, latitude: 1, longitude: 1)
    Coordinates:
    * time                (time) datetime64[ns] 225kB 2007-10-17T11:30:00 ... 2...
    * latitude            (latitude) float64 8B -13.08
    * longitude           (longitude) float64 8B 131.1
    Data variables: (12/142)
    ...
    'Warra': <xarray.Dataset> Size: 191MB
    Dimensions:                  (time: 149851, latitude: 1, longitude: 1)
    Coordinates:
    * time                     (time) datetime64[ns] 1MB 2013-03-05T15:00:00 .....
    * latitude                 (latitude) float64 8B -43.1
    * longitude                (longitude) float64 8B 146.7
    Data variables: (12/210)
    ...
    }


    # Get a subset of 30min dataset, slice to 2 variables and temporal range
    subset = flux_api.get_subset("AdelaideRiver",  "2024_v2", "L3", ["AH", "CO2"], start_time="2009-01-01 12:30")
    >>> <xarray.Dataset> Size: 164kB
    Dimensions:    (time: 6852, latitude: 1, longitude: 1)
    Coordinates:
    * time       (time) datetime64[ns] 55kB 2009-01-01T12:30:00 ... 2009-05-24T...
    * latitude   (latitude) float64 8B -13.08
    * longitude  (longitude) float64 8B 131.1
    Data variables:
        AH         (time, latitude, longitude) float64 55kB ...
        CO2        (time, latitude, longitude) float64 55kB ...
    Attributes: (12/40)
    ...


    # Get a subset of 30min dataset from multiple sites, slice to 2 variables
    subsets= flux_api.get_subsets(["AdelaideRiver", "Warra"],  "2024_v2", "L3", ["AH", "CO2"])
    >>> {'AdelaideRiver': <xarray.Dataset> Size: 674kB
    Dimensions:    (time: 28070, latitude: 1, longitude: 1)
    Coordinates:
    * time       (time) datetime64[ns] 225kB 2007-10-17T11:30:00 ... 2009-05-24...
    * latitude   (latitude) float64 8B -13.08
    * longitude  (longitude) float64 8B 131.1
    Data variables:
        AH         (time, latitude, longitude) float64 225kB ...
        CO2        (time, latitude, longitude) float64 225kB ...
    ...
    'Warra': <xarray.Dataset> Size: 4MB
    Dimensions:    (time: 149851, latitude: 1, longitude: 1)
    Coordinates:
    * time       (time) datetime64[ns] 1MB 2013-03-05T15:00:00 ... 2021-09-21T1...
    * latitude   (latitude) float64 8B -43.1
    * longitude  (longitude) float64 8B 146.7
    Data variables:
        AH         (time, latitude, longitude) float64 1MB ...
        CO2        (time, latitude, longitude) float64 1MB ...
    ...


Some other helper API methods. Refer to API documentation for details.

.. code-block:: python3

    # Get variables of 30min dataset from a site
    flux_api.get_variables("AdelaideRiver")
    >>> ['time', 'latitude', 'longitude', 'crs', 'station_name', 'AH', 'AH_QCFlag', 'AH_HMP_21m', 'AH_HMP_21m_QCFlag', 'AH_IRGA_Av', 'AH_IRGA_Av_QCFlag', 'AH_IRGA_Sd', 'AH_IRGA_Sd_QCFlag', 'AH_IRGA_Vr', 'AH_IRGA_Vr_QCFlag', 'CO2', 'CO2_QCFlag', 'CO2_IRGA_Av', 'CO2_IRGA_Av_QCFlag', 'CO2_IRGA_Sd', 'CO2_IRGA_Sd_QCFlag', 'CO2_IRGA_Vr', 'CO2_IRGA_Vr_QCFlag', 'Fa', 'Fa_QCFlag', 'Fco2', 'Fco2_QCFlag', 'Fe', 'Fe_QCFlag', 'Fg', 'Fg_QCFlag', 'Fg_8cma', 'Fg_8cma_QCFlag', 'Fg_8cmb', 'Fg_8cmb_QCFlag', 'Fh', 'Fh_QCFlag', 'Fld', 'Fld_QCFlag', 'Flu', 'Flu_QCFlag', 'Fm', 'Fm_QCFlag', 'Fn', 'Fn_QCFlag', 'Fsd', 'Fsd_QCFlag', 'Fsu', 'Fsu_QCFlag', 'H2O', 'H2O_QCFlag', 'L', 'L_QCFlag', 'Precip', 'Precip_QCFlag', 'RH', 'RH_QCFlag', 'SH', 'SH_QCFlag', 'SHD', 'SHD_QCFlag', 'Sco2_single', 'Sco2_single_QCFlag', 'Sws', 'Sws_QCFlag', 'Sws_5cma', 'Sws_5cma_QCFlag', 'Sws_5cmb', 'Sws_5cmb_QCFlag', 'Ta', 'Ta_QCFlag', 'Ta_HMP_21m', 'Ta_HMP_21m_QCFlag', 'Ta_SONIC_Av', 'Ta_SONIC_Av_QCFlag', 'Ts', 'Ts_QCFlag', 'Ts_8cma', 'Ts_8cma_QCFlag', 'U_SONIC_Av', 'U_SONIC_Av_QCFlag', 'U_SONIC_Sd', 'U_SONIC_Sd_QCFlag', 'U_SONIC_Vr', 'U_SONIC_Vr_QCFlag', 'VP', 'VP_QCFlag', 'VPD', 'VPD_QCFlag', 'V_SONIC_Av', 'V_SONIC_Av_QCFlag', 'V_SONIC_Sd', 'V_SONIC_Sd_QCFlag', 'V_SONIC_Vr', 'V_SONIC_Vr_QCFlag', 'W_SONIC_Av', 'W_SONIC_Av_QCFlag', 'W_SONIC_Sd', 'W_SONIC_Sd_QCFlag', 'W_SONIC_Vr', 'W_SONIC_Vr_QCFlag', 'Wd', 'Wd_QCFlag', 'Wd_SONIC_Av', 'Wd_SONIC_Av_QCFlag', 'Ws', 'Ws_QCFlag', 'Ws_SONIC_Av', 'Ws_SONIC_Av_QCFlag', 'ps', 'ps_QCFlag', 'ustar', 'ustar_QCFlag']

    # temporal range for 30min dataset (default)
    flux_api.get_temporal_range("AdelaideRiver", "2024_v2", "L6")
    >>> ('2007-10-17T11:30:00.000000000', '2009-05-24T06:00:00.000000000')

    # Get global attributes for 30min dataset from a site
    global_attributes = flux_api.get_global_attributes("AdelaideRiver")
    >>> {'Conventions': 'CF-1.8', 'canopy_height': '16.4m', 'comment': 'CF metadata, OzFlux standard variable names', 'contact': 'jason.beringer@uwa.edu.au', 'coverage_flux_L3': '86%', ... }

    # Get 30min dataset variable's attributes
    var_attributes = flux_api.get_attributes("AdelaideRiver", variables=["AH", "CO2"])
    >>> {'AH': {'coverage_L3': '94%', 'height': '21m', 'instrument': 'HMP45C', 'long_name': 'Absolute humidity', 'standard_name': 'mass_concentration_of_water_vapor_in_air', 'statistic_type': 'average', 'units': 'g/m^3', 'valid_range': array([ 0., 35.])}, 'CO2': {'coverage_L3': '87%', 'height': '21.0', 'instrument': 'Li-7500', 'long_name': 'CO2 concentration', 'standard_name': 'mole_fraction_of_carbon_dioxide_in_air', 'statistic_type': 'average', 'units': 'umol/mol', 'valid_range': array([250., 900.])}}

    # Export dataset as Excel workbook
    flux_api.export_as_excel("/home/user/excel_output.xlxs", "AdelaideRiver", "2024_v2", "L6")

    # Export dataset as oneflux csv format
    flux_api.export_oneflux_csv("/home/user/output_dir", "AdelaideRiver", "2024_v2", "L4")



API Reference
-------------

.. toctree::
    :maxdepth: 2

    api


Version history
----------------

.. toctree::
    :maxdepth: 2

    changelog