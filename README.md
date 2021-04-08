SLI (sly) - Skillet Line Interface from Palo Alto Netowrks

A CLI interface for interacting with skillets

To install:

cd into directory

pip install -e .

type 'sli' to run

Sample commands for reference (needs to be updated before release)

sli load -sd C:\code\bpa_config_test

sli validate -sd C:\code\bpa_config_test --name ironskillet_validation_demo_10_0 -d 172.31.213.10 -u admin

sli configure -sd C:\code\bpa_config_test --name ironskillet_panos_demo_10_0 -d 172.31.213.10 -u admin -cm