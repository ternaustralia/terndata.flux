import terndata.flux as flux


# Get sites where flux data is available
sites = flux.get_sites()
print(sites)

# Get the data versions available for a site
versions = flux.get_versions("AdelaideRiver")
print(versions)

# Get the processing-levels available for a site and version
processing_levels = flux.get_processing_levels("AdelaideRiver", "2024_v2")
print(processing_levels)

# Get 30min datasets from multiple sites
sites = ["AdelaideRiver", "Warra"]
datasets = flux.get_datasets(sites, "2024_v2", "L6")

# Get a 30min dataset from a site, and of a version and processing-level.
ds = flux.get_dataset("AdelaideRiver", "2024_v2", "L3")

# Get variables of 30min dataset from a site
flux.get_variables("AdelaideRiver")

# temporal range for 30min dataset (default)
flux.get_temporal_range("AdelaideRiver", "2024_v2", "L6")

# Get global attributes for 30min dataset from a site
flux.get_global_attributes("AdelaideRiver")

# Get 30min dataset variable's attributes
flux.get_attributes("AdelaideRiver", variables=["AH", "CO2"])

# Get subsets of 30min dataset from multiple sites, slice to 2 variables
subsets = flux.get_subsets(["AdelaideRiver", "Warra"], "2024_v2", "L3", ["AH", "CO2"])
ptint(sites)
