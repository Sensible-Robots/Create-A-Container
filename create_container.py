import tkinter as tk
from tkinter import messagebox, ttk
import requests
from bs4 import BeautifulSoup
import os
import threading
import subprocess

echo_line = 'export PS1=\\"\\[\\033[01;32m\\]Apptainer\\[\\033[00m\\]:\\[\\033[01;33m\\]\\w\\[\\033[00m\\]> \\"'

builder = "singularity" if os.path.isdir("singularity") else "apptainer"

def check_sudo():
    if os.geteuid() != 0:
        # Relaunch the script with sudo
        messagebox.showerror("Permission Required", "This script needs to be run with sudo. Please restart the script with sudo privileges.")
        root.destroy()
        exit()

# Fetch available Python versions from python.org using BeautifulSoup
def fetch_python_versions():
    url = "https://www.python.org/downloads/"
    response = requests.get(url)
    versions = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        releases = soup.find_all("span", class_="release-number")
        for release in releases:
            version = release.get_text(strip=True)
            if version.startswith("Python"):
                versions.append(version)
    return versions

def confirm_requirements_file():
    file_present = os.path.isfile("requirements.txt")
    if file_present:
        return True
    else:
        return False

# Generate Apptainer definition file
def generate_container(python_version, ubuntu_version, build_flag, name="container"):
    python_version_number = python_version.split()[1]
    python_version_short = python_version_number.split('.')[0] + '.' + python_version_number.split('.')[1]
    # Get the absolute path to the requirements.txt file
    current_dir = os.path.abspath(os.path.dirname(__file__))
    requirements_path = os.path.join(current_dir, "requirements.txt")
    definition_content = f"""
Bootstrap: docker
From: ubuntu:{ubuntu_version}

%labels
    Maintainer sensible_robots_lab
    Version 1.0

%files
    # Add your requirements.txt file
    {requirements_path} /opt/requirements.txt    

%post
    # Set noninteractive frontend to avoid interactive prompts
    export DEBIAN_FRONTEND=noninteractive
    # Update and install dependencies
    apt-get update && apt-get install -y \\
        build-essential \\
        wget \\
        libssl-dev \\
        zlib1g-dev \\
        libbz2-dev \\
        libreadline-dev \\
        libsqlite3-dev \\
        curl \\
        llvm \\
        libncurses5-dev \\
        libncursesw5-dev \\
        xz-utils \\
        tk-dev \\
        libffi-dev \\
        liblzma-dev \\
        git
        
    # Set the timezone to UTC (or change to your preferred timezone)
    ln -fs /usr/share/zoneinfo/UTC /etc/localtime
    dpkg-reconfigure --frontend noninteractive tzdata

    # Install Python {python_version_short}
    cd /opt
    wget https://www.python.org/ftp/python/{python_version_number}/Python-{python_version_number}.tgz
    tar xzf Python-{python_version_number}.tgz
    cd Python-{python_version_number}
    ./configure --enable-optimizations
    make altinstall
    ln -s /usr/local/bin/python{python_version_short} /usr/bin/python{python_version_short}

    # Upgrade pip
    python{python_version_short} -m pip cache purge
    python{python_version_short} -m ensurepip
    python{python_version_short} -m pip install --upgrade pip

    # Install requirements

    python{python_version_short} -m pip install -r /opt/requirements.txt
    
    echo "{echo_line}" >> /.singularity.d/env/99-base.sh

%environment
    # Set environment variables
    export PATH="/opt/myenv/bin:$PATH"
    export PYTHON_VERSION={python_version_number}

%runscript
    # Define the default command to run
    exec /bin/bash "$@"
"""

    with open(name+ ".def", "w") as f:
        f.write(definition_content)
    messagebox.showinfo("Success", "Apptainer definition file generated successfully!")
    
    if build_flag:
        build_container(name)
        # close the app after building the container

    else:
        root.quit()

# Function to build the container with a progress bar
def build_container(container_name):
    # Create a new window with a progress bar
    progress_window = tk.Toplevel(root)
    progress_window.title("Building Container")

    tk.Label(progress_window, text="Your container is being built...").pack(pady=10)

    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
    progress_bar.pack(pady=20)
    progress_bar.start()

    # Run the build command in a separate thread to avoid freezing the GUI
    threading.Thread(target=run_build_command, args=(progress_window, progress_bar, container_name)).start()

def run_build_command(progress_window, progress_bar, container_name):
    try:
        build_command = f"sudo {builder} build {container_name}.sif {container_name}.def"
        subprocess.run(build_command, shell=True, check=True)
        progress_bar.stop()
        progress_window.destroy()
        messagebox.showinfo("Success", f"Container '{container_name}.sif' built successfully!")
    except subprocess.CalledProcessError:
        progress_bar.stop()
        progress_window.destroy()
        messagebox.showerror("Error", "Failed to build the container.")
    finally:
        root.destroy()
        exit()

def on_generate():
    selected_python = python_var.get()
    selected_ubuntu = ubuntu_var.get()
    build_container = build_container_var.get()
    name = name_entry.get()
    
    if selected_python and selected_ubuntu:
        if confirm_requirements_file():
            generate_container(selected_python, selected_ubuntu, build_container, name)
        else:
            messagebox.showerror("Error", "requirements.txt not found in the same directory.")
    else:
        messagebox.showerror("Error", "Please select both Python and Ubuntu versions.")



# Fetch Python versions
python_versions = fetch_python_versions()
ubuntu_versions = ["18.04", "20.04", "22.04"]

# Tkinter GUI
root = tk.Tk()
root.title("Apptainer Container Generator")
# Check if running with sudo
check_sudo()

# Python version dropdown
tk.Label(root, text="Select Python Version:").grid(row=0, column=0, padx=10, pady=5)
python_var = tk.StringVar(root)
python_var.set(python_versions[0])  # Set default value
python_menu = tk.OptionMenu(root, python_var, *python_versions)
python_menu.grid(row=0, column=1, padx=10, pady=5)

# Ubuntu version dropdown
tk.Label(root, text="Select Ubuntu Version:").grid(row=1, column=0, padx=10, pady=5)
ubuntu_var = tk.StringVar(root)
ubuntu_var.set(ubuntu_versions[2])  # Set default value
ubuntu_menu = tk.OptionMenu(root, ubuntu_var, *ubuntu_versions)
ubuntu_menu.grid(row=1, column=1, padx=10, pady=5)

# Name entry
tk.Label(root, text="Name:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
name_entry = tk.Entry(root)
name_entry.grid(row=3, column=0, padx=10, pady=5, columnspan=2, sticky="n")

# Yes/No for building the container
build_container_var = tk.BooleanVar()
build_container_var.set(1)
build_container_check = tk.Checkbutton(root, text="Build container after generating def file", variable=build_container_var)
build_container_check.grid(row=4, column=0, padx=10, pady=5, sticky="w")

# Generate button
generate_button = tk.Button(root, text="Generate Container", command=on_generate)
generate_button.grid(row=5, columnspan=2, pady=20)

root.mainloop()
