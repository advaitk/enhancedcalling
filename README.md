# enhancedcalling
Automate enabling of Enhanced Calling mode for Cisco Webex Cloud registred, personal mode devices 

## Overview
Enhanced Calling allows users to utilize PSTN dialing on video devices when registered on Webex Cloud in Personal Mode. Previously, Cisco completed EOL on some hybrid services for Webex Cloud registered devices, then Personal mode devices lost their inbound and outbound PSTN calling capabilities.

Cisco has an interim/stop-gap solution to address the gap in functionality, called Enhanced Calling, which brings back PSTN capability for those users with Personal mode devices.

This code is a demonstration of how Enhanced Calling can be enabled, using On Premise UCM deployment. And is meant for educational/information purposes only.

Some changes might be required to fit the deployment and configurations of your particular environment.

Some of the APIs used in these examples are not "public" APIs. Meaning, they are not published at https://developer.webex.comand are subject to change without notice from Cisco.
But these are the same APIs that Control HUB UI makes use of.
## Installation/Setup
* Install Python 3

    On Windows, choose the option to add to PATH environment variable

* (Optional) Create/activate a Python virtual environment named `venv`:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
* Install needed dependency packages:

    ```bash
    pip install -r requirements.txt
    ```

* Rename `.env.example` to `.env`, and edit it to specify your values CUCM address, AXL user credentials, ORG Id, Bearer token from Control Hub.

* (Optional) The AXL v12.5 WSDL files are included in this project.  If you'd like to use a different version, replace with the AXL WSDL files for your CUCM version:

    1. From the CUCM Administration UI, download the 'Cisco AXL Tookit' from **Applications** / **Plugins**

    1. Unzip the kit, and navigate to the `schema/current` folder

    1. Copy the three WSDL files to the `schema/` directory of this project: `AXLAPI.wsdl`, `AXLEnums.xsd`, `AXLSoap.xsd`


## Usage
* Help

    ```bash
    python3 runner.py --help
    Usage: runner.py [OPTIONS]

    Options:
      --userid TEXT     Userid not email
      --devicemac TEXT  format 'AA:BB:CC:DD:EE:FF'
      --help            Show this message and exit.
    ```

* Single run

    ```bash
    python3 runner.py --userid advaitk --devicemac AA:BB:CC:DD:EE:FF
    ```

* Multi run
  
  ```bash
  #Create a csv file with userid and devicemac as rows, for e.g.
  cat list.csv
  userid1,AA:BB:CC:DD:EE:F1
  userid2,AA:BB:CC:DD:EE:F2
  userid3,AA:BB:CC:DD:EE:F3
  
  #And then invoke the runner.py command using this bash snippet
  while IFS=, read -r userid devicemac
  do
      echo "Invoking using userid : $userid : device mac $devicemac"
      python3 runner.py --userid $userid --devicemac $devicemac
  done < list.csv
  ```
