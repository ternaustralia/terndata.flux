from datetime import datetime

import defusedxml.ElementTree as ET
import requests

# default dataset is 30-min
DEFAULT_DATASET = "30min"

# namespaces
xmlns = "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}"
xlinkns = "{http://www.w3.org/1999/xlink}"

# Session for request, with User-Agent header
session = requests.Session()
session.headers.update({"User-Agent": "TERN-DATA-PACKAGE/flux-api"})


# TODO: pass in API-name that calls this function to be embedded in user-agent,
# allowing more detail stats on API calls?
def get_catalog_items(url: str, itype: str = "catalogRef") -> dict[str, str]:
    """Get catalog items and their associated reference links (URL) from the catalog XML document.

    Args:
        url: The catalog XML document URL.
        itype: item type to look for in the catalog, dataset or catalogRef. Default to catalogRef.

    Returns:
        A dictionary of catalog items and associated reference links (URL).
    """
    resp = session.get(url)
    resp.raise_for_status()
    tree = ET.fromstring(resp.text.encode(), forbid_dtd=True)
    references = {}
    for ref in tree.iter(f"{xmlns}{itype}"):
        item = ref.attrib
        if itype == "catalogRef":
            references[item["name"]] = url.replace("catalog.xml", item[f"{xlinkns}href"])
        else:
            # dataset name: i.e. AdelaideRiver_L6_Daily.nc
            # This assumes daily, monthly datasets, etc end with daily, monthly, etc in their
            # dataset name.
            name = item["name"]
            if name.endswith(".nc"):
                parts = name[:-3].split("_")
                ds_name = DEFAULT_DATASET
                if len(parts) >= 3 and parts[-1].lower() in [
                    "daily",
                    "monthly",
                    "annual",
                    "cumulative",
                    "summary",
                ]:
                    ds_name = parts[-1].lower()
                references[ds_name] = url.replace("catalog.xml", item["name"]).replace(
                    "/catalog/", "/dodsC/"
                )
    return references


def get_catalog_url(obj: str, params: dict = {}) -> str:  # noqa: B006
    """Get a catalog access URL for the object with parameters specified.

    Args:
        obj: {"site", "version", "processing_level", "dataset"}
             The catalog item object.
        params: catalog object parameters . Defaults to {}.

    Raises:
        ValueError: Invalid catalog item object exception.

    Returns:
        A catalog access URL for the object specified.

    Raises:
        ValueError: An exception for invalid catalog item.
    """
    # TERN Flux data catalog access URL
    url = "https://dap.tern.org.au/thredds/catalog/ecosystem_process/ozflux/{}catalog.xml"

    url_subpath = {
        "site": "",
        "version": "{site}/",
        "processing_level": "{site}/{version}/",
        "dataset": "{site}/{version}/{processing_level}/default/",
    }
    if obj not in url_subpath:
        raise ValueError(f"Invalid '{obj}' catalog item object")
    subpath = url_subpath.get(obj).format_map(params)
    return url.format(subpath)


def get_dataset_urls(site: str, version: str, processing_level: str) -> dict[str, str]:
    """Get the access URLs for the datasets for the specified site, version and processing-level.

    Args:
        site: site name
        version: version of the dataset
        processing_level: processing level of the dataset

    Returns:
        The access URLs for the datasets.
    """
    cat_url = get_catalog_url(
        "dataset", params={"site": site, "version": version, "processing_level": processing_level}
    )
    return get_catalog_items(cat_url, itype="dataset")


def is_isoformat(date_str: str) -> bool:
    """Check if the specified date string is in ISO format.

    Args:
        date_str: ISO formatted date string

    Returns:
        True if date string is in ISO format. Otherwise False.
    """
    try:
        _ = datetime.fromisoformat(date_str)
        return True
    except Exception:  # noqa: PIE786
        return False
