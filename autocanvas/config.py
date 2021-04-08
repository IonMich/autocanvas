# settings.py
import os
from os.path import join, dirname
from pathlib import Path
from dotenv import load_dotenv

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
TOPLEVEL_DIR = str(Path(PACKAGE_DIR).parent.absolute())
INPUT_DIR = join(PACKAGE_DIR, "input")
OUTPUT_DIR = join(PACKAGE_DIR, "output")


def get_API_key():
    dotenv_path = join(TOPLEVEL_DIR, '.env')
    load_dotenv(dotenv_path)

    API_KEY = os.environ.get("API_KEY")

    if API_KEY is None:
        raise FileNotFoundError("A `.env` file was not found. You need "
                            "to create a `.env` inside the top-level " 
                            "directory (same dir as requirements.txt) and add a single entry:\n\n"
                            "API_KEY=<value>\n\nSubstitute <value> with "
                            "your API key. You can find more info in the wiki.")
    else:
        return API_KEY
