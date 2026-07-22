# Tips for using Traitlets

A collection of useful design tips for using traitlets in your
application or library.

## Avoid using "pure config" objects

Put your traitlets config directly on the classes that are doing the work,
rather than creating separate classes just for holding configuration. This
keeps configuration close to the code it is configuring, and helps with
discoverability as well.

So instead of:

```python
class SpawnerConfig(LoggingConfigurable):
    some_config = Unicode(
        "",
        config=True
    )

    some_other_config = Unicode(
        "default",
        config=True
    )

class Spawner:
    def spawn(self, config: SpawnerConfig):
        print(config.some_config)
        # Do things with config

```

Prefer:

```python
class Spawner(LoggingConfigurable):
    some_config = Unicode(
        "",
        config=True
    )

    some_other_config = Unicode(
        "default",
        config=True
    )

    def spawn(self):
        print(self.some_config)
```