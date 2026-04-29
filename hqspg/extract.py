from .extractor import extract_samples

def extract(stems, output_base, track_name, config=None):
    return extract_samples(stems, output_base=output_base, track_name=track_name, config=config)
