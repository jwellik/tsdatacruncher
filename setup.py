from setuptools import setup, find_packages

setup(
    name="tsdatacruncher",
    version="0.1.0",
    description="Crunch time series data like a boss.",
    author="Jay Wellik",
    author_email="jwellik@usgs.gov",
    url="https://github.com/jwellik/tsdatacruncher",
    packages=find_packages(),  # Automatically finds all submodules
#    install_requires=requirements,
   install_requires=[
       "obspy",              # solid codebase for seismology
       "bokeh",              # visualization
       "psutils",            # system monitoring
   ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
