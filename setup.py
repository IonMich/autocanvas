from setuptools import setup, find_packages

def get_requirements():
    with open("requirements.txt", "r") as ff:
        requirements = ff.readlines()
    return requirements


VERSION = "0.1"

setup(name='autocanvas', 
      version=VERSION, 
      author='Ioannis Michaloliakos',
      author_email='ioannis.michalol@ufl.edu',
      python_requires='>=3.7',
      requirements=get_requirements(),    
      packages=['autocanvas', 'autocanvas.core'],
      package_dir={'autocanvas': 'autocanvas'})

      
