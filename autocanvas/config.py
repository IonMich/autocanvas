# settings.py
import os
from os.path import join, dirname
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = join(ROOT_DIR, "input")
OUTPUT_DIR = join(ROOT_DIR, "output")


def get_API_key():
    dotenv_path = join(INPUT_DIR, '.env')
    load_dotenv(dotenv_path)

    API_KEY = os.environ.get("API_KEY")

    if API_KEY is None:
        raise FileNotFoundError("A `.env` file was not found. You need "
                            "to create a `.env` inside the `input` " 
                            "directory and add a single entry:\n\n"
                            "API_KEY=<value>\n\nSubstitute <value> with "
                            "your API key. You can find more info in the wiki.")
    else:
        return API_KEY