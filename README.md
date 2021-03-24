# enhancedcalling

## Overview
With Cisco EOL'ing some hybrid services for Webex Cloud registered devices, Personal mode devices lost their PSTN calling capabilities, both inbound and outbound.

Cisco has an interim/stop-gap solution, to address this gap in functionality, called Enhanced Calling.
This is a demonstration of how Enhanced Calling can be enabled, using On Premise UCM deployment.

The API used in these examples are not "public" APIs. Meaning, they are not published at https://developer.webex.com and are subject to change without notice from Cisco.

But these are the same APIs that Control HUB UI makes use of.
The intent of this script is to solve the short term problem, till we get a more longer term solution.
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
