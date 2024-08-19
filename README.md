# Container Creation Tutorial
Author: Peter Tisnikar

Last Updated: 19 August 2024

*NOTE: This tutorial is a work in progress, and contributions of any kind are more than welcome. Please contact the author to discuss possible contributions and topics you would like to see included in the future.*

Welcome to this tutorial on creating containers that we can use on the [RAP Workstation](https://github.com/Sensible-Robots/Workstation-Experiments) or on KCL's [CREATE HPC cluster](https://docs.er.kcl.ac.uk/).

To make creation of containers as easy as possible, I have prepared a script which is available in this repository, along with a set of instructions on how to use it to create your containers. This tutorial goes over this process, so keep reading if you want to create your own container!

## System Support

This tutorial was written for, and tested on, an Ubuntu machine. I will not support other operating systems and I encourage you to find your own solutions if you wish to use them.

## Requirements

In order to be able to run the script, you must have either Singularity or Apptainer installed on your machine, on which you will also need sudo privileges.

I ***strongly*** recommend installing Apptainer as an Ubuntu package, either by using the provided ```install_update_apptainer.sh``` script (with thanks to its creator Gerard Canal), or as shown [here](https://apptainer.org/docs/admin/1.2/installation.html). Singularity does not have pre-built Ubuntu packages and its installation is a lot more involved. Apptainer is also newer, and is the system that runs both on the RAP Workstation as well as the CREATE HPC cluster.

Once you've installed Apptainer, you can move on to creating containers with the script. The script should only contain libraries that are standard Python libraries and come included with a fresh Python installation. If your script does not work because of an import error, carefully read what it says and ```pip install``` the appropriate library.

## Container Script Usage

To generate containers using this script, first clone this repository like so:
```
git clone https://github.com/Sensible-Robots/Create-A-Container.git
```
As you will see, there are 3 files in the repository: a Bash script to install Apptainer (discussed above), the main Python script, and a ```requirements.txt file```.

In order to create a container with Python libraries that you want to use within it, you need to either modify or replace the ```requirements.txt``` file with your own dependencies. **NOTE: It is important that you do not rename the file, as the script will not be able to find it!**

To create your own requirements file with libraries that you want to install, you can use the following command in the Python environment on your machine that you set up for this particular experiment:
```
cd Create-A-Container && pip freeze > requirements.txt
```
This command will overwrite the requirements file in the folder with your own requirements. You can then further manually edit the requirements file if you wish.

When running the script, make sure to use ```sudo``` privileges, like so:
```
sudo python3 create_container.py
```
This will start the application's GUI. If you do not run it with ```sudo``` privileges, the script will prompt you to re-run it and will close itself. This is deliberate, as container building needs sudo privileges.

Next, you will see a GUI window asking you to pick your Python version out of all of the available versions on the Python website, and the Ubuntu version, where you can choose from 18.04, 20.04, and 22.04. If you do not have any restrictions in terms of libraries you are using, it is recommended you leave the Python and Ubuntu versions as defaults. There is also an input window asking you to name your container. The container's definition file and the SIF file will have the same name if you build your container using the script. Lastly, there is a checkbox asking you if you wish to build the container. If you untick it, you will only generate the container's definition file, and you can build the container later yourself using ```sudo apptainer build <CONTAINER_NAME>.sif <DEF_FILE_NAME>.def``` command. If you leave the box ticked, the script will run this command for you.

The container building may take some time, but the script will notify you when the building process is finished. You will then be able to find both a definition and a SIF file in the script folder. You can verify the installation of libraries by running the container and calling ```pip list``` once inside it.

## Going Beyond Requirements

It is possible that you will need to add libraries that do not exist as packages on PyPI, and therefore cannot be installed using pip. If this is the case, you will have to manually edit the definition file and add in the dependencies in the ```%post``` section of the definition file. Below you can find an example of adding some additional ```apt-get``` installs and a Github-based library to the definition file:
```
%post
    # Set noninteractive frontend to avoid interactive prompts
    export DEBIAN_FRONTEND=noninteractive
    
    # Update and install dependencies
    apt-get update && apt-get install -y \
        build-essential \
        wget \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        curl \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        libffi-dev \
        liblzma-dev \
        git \
        python3-opengl \
        mesa-utils \
        xvfb
        
    # Set the timezone to UTC (or change to your preferred timezone)
    ln -fs /usr/share/zoneinfo/UTC /etc/localtime
    dpkg-reconfigure --frontend noninteractive tzdata

    # Install Python 3.10
    cd /opt
    wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
    tar xzf Python-3.10.14.tgz
    cd Python-3.10.14
    ./configure --enable-optimizations
    make altinstall
    
    # Ensure the symbolic link creation doesn't fail
    if [ -f /usr/bin/python3.10 ]; then
        rm /usr/bin/python3.10
    fi
    ln -s /usr/local/bin/python3.10 /usr/bin/python3.10

    # Upgrade pip and install virtualenv
    python3.10 -m ensurepip
    python3.10 -m pip install --upgrade pip==24.0

    # Create a virtual environment and install requirements
    if [ -f /home/mazegym_containers/requirements.txt ]; then
    	python3.10 -m pip install setuptools==66 wheel==0.38.4
        python3.10 -m pip install -r /home/mazegym_containers/requirements.txt
    fi
    
    # Install IL-Datasets module
    cd /opt
    git clone https://github.com/NathanGavenski/IL-Datasets/ 
    cd \IL-Datasets
    python3.10 -m pip install -e .[benchmark]
    
    echo "export PS1=\"\[\033[01;32m\]Apptainer\[\033[00m\]:\[\033[01;33m\]\w\[\033[00m\]> \"" >> /.singularity.d/env/99-base.sh
```

