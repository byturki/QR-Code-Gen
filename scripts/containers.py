"""Canonical department -> container mapping for kpcwebsitestorageaccount.

This list mirrors the actual containers in Azure (verified via `az storage
container list`). Update it here if containers are added/renamed in Azure.
"""

# name: the real Azure container name
# public_access: "container" (anonymous read + list), "blob" (anonymous read,
#   no list), or None (private - not suitable for public QR codes)
# aliases: free-text terms a user might type when describing the department
CONTAINERS = [
    {"name": "corporaterelations", "public_access": "container",
     "aliases": ["corporate relations", "corp relations", "cr"]},
    {"name": "employees-development", "public_access": "blob",
     "aliases": ["employee development", "employees development", "training",
                 "learning and development", "l&d"]},
    {"name": "empoweringcommunities", "public_access": "container",
     "aliases": ["empowering communities", "csr", "community", "communities"]},
    {"name": "emtazcompanies", "public_access": "container",
     "aliases": ["emtaz", "emtaz companies"]},
    {"name": "hrmedia", "public_access": "container",
     "aliases": ["hr", "human resources", "hr media"]},
    {"name": "hsse", "public_access": "blob",
     "aliases": ["hsse", "health safety security environment", "safety"]},
    {"name": "indexsliders", "public_access": "container",
     "aliases": ["index sliders", "sliders", "homepage sliders"]},
    {"name": "inforequests", "public_access": None,
     "aliases": ["info requests", "information requests"]},
    {"name": "media", "public_access": "container",
     "aliases": ["media", "press", "news"]},
    {"name": "ptc", "public_access": "container", "aliases": ["ptc"]},
    {"name": "publications", "public_access": "container",
     "aliases": ["publications", "publication", "reports"]},
    {"name": "publicstatements", "public_access": "container",
     "aliases": ["public statements", "press releases", "statements"]},
    {"name": "recruitment", "public_access": "container",
     "aliases": ["recruitment", "careers", "jobs", "hiring"]},
    {"name": "research-technology", "public_access": "blob",
     "aliases": ["research", "technology", "research and technology", "r&d"]},
    {"name": "services-commercial", "public_access": "blob",
     "aliases": ["services", "commercial", "services and commercial"]},
    {"name": "topmanagments", "public_access": "container",
     "aliases": ["top management", "management", "executives", "leadership"]},
    {"name": "uploads", "public_access": "container",
     "aliases": ["uploads", "general", "misc"]},
]

CONTAINER_NAMES = [c["name"] for c in CONTAINERS]
