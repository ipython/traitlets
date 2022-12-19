# Example config used by load_config_app.py

c = get_config()  # noqa

# Load everything from base_config.py
load_subconfig('base_config.py')  # noqa

# Now override one of the values
c.MyClass.name = 'bettername'
