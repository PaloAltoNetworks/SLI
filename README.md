SLI (sly) - Skillet Line Interface from Palo Alto Netowrks

A CLI interface for interacting with skillets

**To install:**

cd into directory

pip install -e .

type 'sli' to run

**To install for MAC:**

cd into local directory

run 'git clone git@gitlab.com:panw-gse/as/sli.git'

cd into sli directory

python3 -m venv ./venv

source ./venv/bin/activate

pip install -e .

python cli.py

**Sample commands for reference (needs to be updated before release)**

sli load -sd C:\code\bpa_config_test

sli validate -sd C:\code\bpa_config_test --name ironskillet_validation_demo_10_0 -d 172.31.213.10 -u admin

sli configure -sd C:\code\bpa_config_test --name ironskillet_panos_demo_10_0 -d 172.31.213.10 -u admin -cm
