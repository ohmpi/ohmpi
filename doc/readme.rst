To compile the documentation:

Copy a default config just to be able to instantiate the ohmpi class, then build the doc.

```bash
cp configs/config_default.py ohmpi/config.py
cd doc/
rm -r build
sphinx-build source build
```

