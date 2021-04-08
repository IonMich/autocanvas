# autocanvas
Code to automate actions on Canvas using CanvasAPI

# Description
The CanvasAPI and its python wrapper provide a powerful framework to automate repetitive actions on the Canvas platform for teachers. In this repository we expand on these methods and we create pipelines to perform a variety of common teaching tasks, such as scheduling quizzes and exams, as well as creating summary statistics and plots. The routines have been designed (but not restricted) to work best with large auditorium courses at the Physics Department the University of Florida.

# Getting started
The easiest way to make use of this codebase is by reading the Jupyter Notebooks in the `pipes` and `tests` folders.  There you can find a step by step implementation of many pipelines. **NOTE**: before you can run these codes, you will need to install this package, by navigating to the directory where `setup.py` resides, and running:

```
conda install ipykernel
conda install pip
pip install -e .
```

In the future, a non-interactives way of running these pipelines might be offered.

## Creating an API key
The CanvasAPI library gives access to restricted information present on Canvas Course, which is available only to Canvas users with the appropriate permissions (e.g. teaching personel, course designers). As a result, authentication is needed to access this information. This comes in the form of API keys. The official Canvas API documentation page provides a lot of information on how to generate one. As described there, the simplest method of generating one is the following:

1. Go on Canvas and click the "profile" link in the top right menu bar, or navigate to /profile
2. Under the "Approved Integrations" section, click the button to generate a new access token.
3. Once the token is generated, you cannot view it again, and you'll have to generate a new token if you forget it. Remember that access tokens are password equivalent, so keep it secret.

## Storing an API key
In order to avoid having to generate the API key everytime you run the code, store the API key in an environment file named `.env` in the top-level folder (i.e. alongside the `requirements.txt` file). This file should include an entry:

```
API_KEY=<value>
```

# Main Features
The CanvasAPI library returns a `PaginatedList` of python objects after each call to its methods, which are not easy to handle and manipulate. Here we convert these to pandas `DataFrames`, which are ideally suitted for the data processing actions we want perform in Canvas.  

Implemented Pipelines:
- Create section overrides for all weekly quizzes.
- Fix the grade of individual questions of a Quiz assignment.
- Create summary plots for weekly quiz grading, grouped by Teaching Assistant (TA).
- Get summary statistics (mean, std) for quiz scores grouped by TA.
- Create quiz overrides for groups of students, based on their section.

# Dependencies
Some of the main dependencies of the code are:
- `selenium`>=3.141.0
- `canvasapi`>=2.2.0
- `pandas`>=1.2.3
- `openpyxl`
- `ipykernel`
- `beautifulsoup4`>=4.9.3
- `lxml`
- `python-dotenv`>=0.17.0
- `aiohhtp`
- `seaborn`
- `tabulate`



# Known Issues
