# Example config used by load_config_app.py
from __future__ import annotations

c = get_config()  # noqa: F821

# Load everything from base_config.py
load_subconfig("base_config.py")  # noqa: F821

# Now override one of the values
c.School.name = "Caltech"
