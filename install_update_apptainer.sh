#!/bin/bash
_get_latest_release() { 
  # From: https://gist.github.com/lukechilds/a83e1d7127b78fef38c2914c4ececc3c
  curl --silent "https://api.github.com/repos/$1/releases/latest" | # Get latest release from GitHub api
    grep '"tag_name":' |                                            # Get tag line
    sed -E 's/.*"([^"]+)".*/\1/'                                    # Pluck JSON value
}

install_apptainer() {
  echo "Installing Apptainer $APPTAINER_VERSION"
  rm /tmp/apptainer*deb*
  wget https://github.com/apptainer/apptainer/releases/download/$APPTAINER_VERSION/apptainer_${APPTAINER_VERSION:1}_amd64.deb -P /tmp/ -q --show-progress
  sudo apt install -y --allow-downgrades /tmp/apptainer_${APPTAINER_VERSION:1}_amd64.deb
}


# Note, to install a specific version comment the following line
APPTAINER_VERSION=$(_get_latest_release apptainer/apptainer)
# For instance, to install version v1.1.4, uncomment the following line (change it for the version to install)
#APPTAINER_VERSION=v1.1.4

INSTALLED_VERSION=$(dpkg -l | grep apptainer | awk '{print $3;}')
if [[ -z $INSTALLED_VERSION ]]; then # INSTALLED_VERSION is empty
  install_apptainer
elif [[ "$INSTALLED_VERSION" != "${APPTAINER_VERSION:1}" ]]; then
  echo "Update for apptainer available!"
  echo "   INSTALLED_VERSION version: v$INSTALLED_VERSION"
  echo "   Latest version:    $APPTAINER_VERSION"
  install_apptainer
else
  echo "apptainer is up to date (v$INSTALLED_VERSION)."
fi
