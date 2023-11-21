import warnings

def measure(self, **kwargs):
    warnings.warn('This function is deprecated. Use run_multiple_sequences() instead.', DeprecationWarning)
    self.run_multiple_sequences(**kwargs)

def read_quad(self, **kwargs):
    warnings.warn('This function is deprecated. Use load_sequence instead.', DeprecationWarning)
    self.load_sequence(**kwargs)

def stop(self, **kwargs):
    warnings.warn('This function is deprecated. Use interrupt instead.', DeprecationWarning)
    self.interrupt(**kwargs)

def _update_acquisition_settings(self, config):
    warnings.warn('This function is deprecated, use update_settings() instead.', DeprecationWarning)
    self.update_settings(settings=config)