# terndata.flux

This is a Python package to work with TERN flux data. It provides API methods to explore and access flux datasets from the TERN THREDDS/DAP server (i.e. dap.tern.org.au).

### Build
Buid the package wheel locally (docker required):
    
    make build

Build the API documentation:

    make doc

To run unittests:

    make test

    OR
    
    Run the script below:
        ./ci-scripts/run-tests.sh

### Installation
Install from repository:

    pip install git+https://github.com/ternaustralia/terndata.flux

### API Methods
See the [API documentation](./docs/api_doc/html/index.html) generated from the code (see above).

### Getting started
The following examples are provided to help you get started, with sample output (as indicated by >>>) where appropriate:

    import terndata.flux as flux 
    # Get sites where flux data is available
    flux.get_sites()
    >>> site           longitude   latitude  ...                start                  end                     geometry
    AdelaideRiver      131.117800 -13.076900  ...  2007-10-17 11:30:00  2009-05-24 06:00:00    POINT (131.1178 -13.0769)
    AliceSpringsMulga  133.249000 -22.283000  ...  2010-09-03 00:00:00  2025-01-28 10:00:00      POINT (133.249 -22.283)
    AlpinePeatland     147.320833 -36.862222  ...  2017-04-12 18:30:00  2022-06-20 23:30:00  POINT (147.32083 -36.86222)
    Boyagin            116.938559 -32.477093  ...  2017-10-20 13:00:00  2025-02-02 00:00:00  POINT (116.93856 -32.47709)
    ...

    # get the versions available for the site
    versions = flux.get_versions("AdelaideRiver")
    >>> ['2020', '2021_v1', '2022_v1', '2022_v2', '2023_v1', '2023_v2', '2024_v1', '2024_v2']
    
    # Get the processing-levels available for a site and version
    processing_levels = flux.get_processing_levels("AdelaideRiver", "2024_v2")
    >>> ['L3', 'L4', 'L5', 'L6']

    # Get a 30min dataset from a site, and of a version and processing-level.
    30min_ds = flux.get_dataset("AdelaideRiver", "2024_v2", "L3")
    >>> <xarray.Dataset> Size: 18MB
    Dimensions:             (time: 28070, latitude: 1, longitude: 1)
    Coordinates:
    * time                (time) datetime64[ns] 225kB 2007-10-17T11:30:00 ... 2...
    * latitude            (latitude) float64 8B -13.08
    * longitude           (longitude) float64 8B 131.1 
    ...

    # Get a daily dataset
    daily_ds = get_l6_daily("AdelaideRiver", "2024_v2")

    # Get 30min datasets from multiple sites
    sites = ["AdelaideRiver", "Warra"]
    flux.get_datasets(sites, "2024_v2", "L6")
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

    # Get a subset of 30min dataset from multiple sites, slice to 2 variables
    flux.get_subsets(["AdelaideRiver", "Warra"],  "2024_v2", "L3", ["AH", "CO2"])
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

    # Export dataset as Excel workbook
    flux.export_as_excel("/home/user/excel_output.xlxs", "AdelaideRiver", "2024_v2", "L6")
    >>> '/home/user/excel_output.xlxs'

    # Export dataset as oneflux csv format
    flux.export_oneflux_csv("output_dir", "AdelaideRiver", "2024_v2", "L4")
    >>> ['output_dir/AU-Adr_qcv_2007.csv', 'output_dir/AU-Adr_qcv_2008.csv', 'output_dir/AU-Adr_qcv_2009.csv']
    
### Dependencies

* xarray
* netcdf4
* packaging
* numpy
* pandas
* requests
* matplotlib
* defusedxml
* xlsxwriter
* xlrd

### Who do I talk to?

* Repo owner or admin
* Other community or team contact
