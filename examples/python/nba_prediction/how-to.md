# How to use
This project has only been developed and tested in vscode and the below instructions will reflect that.

To run and develop this project the the following steps should be executed:
1. Create a conda environment with the command <b>conda create -n ENV-NAME python=PYTHON-VERSION</b>
2. Activate the created conda environment with the commdan <b>conda activate ENV-NAME</b>
3. Install the pyspark package version 3.2.1 from conda-forge into the conda environment using the command <b>conda install -c conda-forge pyspark==3.2.1</b>
4. Set the python interpeter used in vscode to the python.exe found in the conda environment folder.

The delta lake jars are added to the spark jars folder as part of building the docker image, which is why the delta-spark package does not need to be installed and why there is also no need for configuring the spark session with configure_spark_with_delta_pip().

The above steps generally needs to be performed whenever a project has been opened in a new docker container.
