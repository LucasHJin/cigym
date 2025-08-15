import os

OUTPUT_DIR = "io_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def add_io_dir(filename):
    """Return the full path for a file in the output folder."""
    return os.path.join(OUTPUT_DIR, filename)