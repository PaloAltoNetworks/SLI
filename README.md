# SLI

  

SLI (sly) - Skillet Line Interface from Palo Alto Networks

  

A CLI interface for interacting with skillets. Skillets are sharable sets of configuration elements for PAN-OS devices.
See [Live](https://live.paloaltonetworks.com/t5/quickplay-solutions-discussions/the-palo-alto-networks-skillet-story/m-p/308056)
for more information.

Vist the [SkilletBuilder](https://github.com/PaloAltoNetworks/SkilletBuilder) project for information about skillets, sample skillets,
and documentation related to skillets.
  

## Installation

  

It is recommended to install SLI in a venv to avoid conflicts with other python packages

  

The latest release of SLI is availble on pip, install with

```
pip install sli
```

  

Upgrade with

```
pip install sli --upgrade
```

  

To get the latest development version SLI, install by cloning this repository and running these commands with an active venv

```
 # Change into the cloned directory

cd into directory

 # The "." at the end allows you to edit the code and use the sli command

pip install -e .
```
Installing the development version for mac users and linux that requires the "python3" command to use python version 3, run these commands
```
git clone git@gitlab.com:panw-gse/as/sli.git
cd sli
python3 -m venv ./venv
source ./venv/bin/activate
pip install -e .
```
  
  To test any installation of SLI, with your venv activated run "sli", or "sli --help" to see available commands

## Loading Skillets

When SLI is run, if your command requires skillets, they are all loaded from your working directory by default, unless
you specify otherwise. Test loading skillets with the following command. This command changes nothing in your 
sli environment, the -sd parameter (skillet directory) is supported by all commands that require skillets.

```
 # Load and view skillets from current working directory
sli load

 # Load and view skillets from a specified command
sli load -sd C:\code\skillets\iron-skillet\
```

## Running skillets

The primary purpose of SLI is to execute skillets, here is configuration skillet example:
```
 # The configure command requires a single skillet to be selected
 # This can be done with the --name parameter
sli configure -sd C:\skillets --name skillet_name
```
Validation example
```
sli validate -sd C:\skillets --name skillet_name
```
Both of the above commands will prompt the user for a target host, username and password. 
Those can be provided through the command using parameters
```
sli validate -sd C:\skillets --name skillet_name -d device_ip -u username -p password
```

# Context Manager

SLI has a context manager that allows data to be stored and reused between subsequent commands. 
Context data is stored in disk in your home directory under ".sli/".

You can use the context manager by specifying the -uc flag in your SLI commands
```
sli validate -sd C:\skillets --name skillet_name -uc
```
This will populate the default context with output from the skillet, including configuration and device credentials. 
If the default context is already populated, that data will be loaded prior to execution only because the -uc flag is 
present.

As device credentials are stored in the context, you only need to specify them during the first command when using 
the context manager.

| :exclamation:  By default, the context files are NOT encrypted!   |
|:-------------------------------------------------------------------|
| See `Context Encryption` below to ensure your device credentials or other sensitive information is protected! |

## Named Contexts

You can store data in multiple named contexts other than the default to be able to test multiple configurations at 
once using the -cn parameter
```
 # When specifying -cn, you do not need -uc
 # This will store all context data in a context named my_context
sli validate -sd C:\skillets --name skillet_name -cn my_context
```
Subsequent commands using the same -cn parameter will load context from the specified context name.

## Managing contexts

You can view all contexts stored on your system with 
```
sli list_context
```
If you want to view the contents of a context run
```
sli show_context my_context
 # Leaving out my_context will print the default context
```
You can also clear an existing context with
```
sli clear_context my_context
```
As context output can get quite long when storing the entire configuration XML, you can filter this from output with the -nc flag
```
sli show_context -nc
```

## Context Encryption

Context data is not encrypted on disk by default. You can however encrypt your context by adding an encryption 
password with the -ec (encrypt-context) flag or -cp (context-password) parameter
```
 # This will prompt you for an encryption password
sli validate -sd C:\skillets --name skillet_name -ec

 # This sets the context password to context_password
sli validate -sd C:\skillets --name skillet_name -cp context_password
```
When accessed after creation, an encrypted context will prompt the user for the password unless specified with the 
-cp parameter.

An unencrypted context can be encrypted by specifying encryption when running a command that uses a given context, 
this cannot be undone.

## Commands

  Other than executing skillets, certain commands are available which are useful for skillet development and shell 
  scripting. The context manager is supported for commands that perform data retrieval and processing
  
  The capture command allows you to test capture_list, capture_object, and capture_expression snippets as they would 
  be used in validation skillets
  ```
 # Test and output a capture_list that displays names of all decryption policies
sli capture list  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry/rulebase/decryption/rules/entry/@name"

 # Same as above, except this command will store the output to the default context in the variable "decryption_rules"
sli capture -uc list "/config/devices/entry[@name='localhost.localdomain']/vsys/entry/rulebase/decryption/rules/entry/@name" -cv decryption_rules

 # Capturing an object works similar to capturing a list
sli capture object "/config/devices/entry[@name='localhost.localdomain']/vsys/entry/rulebase/decryption"

 # Capturing an expression allows further processing on data already stored in the context
sli capture -uc expression "decryption_rules | json_query('[].entry[].category.member[]')"

 # Windows requires an additional escape character on double quotes, a ` is required in addition to the \
 sli capture -uc expression "decryption_obj | json_query('decryption.rules.entry[].\`"@name\`"')"


  ```
When using the capture command, escapings strings can make things difficult for more involved quries. You can also omit
the query, and sli will prompt you for it literally, with no escaping required
  ```  
sli capture -uc expression -cv test_out

capture_expression: sec_rules | json_query('[].rules.entry[? @."@name" == `web_browsing`].action[]')
Output added to context as test_out
[
    "allow"
]
  ```

SLI can also provide a diff of the candidate and running config to provide an xpath / XML combo.
```
 # This command gets the device credentials from the default context and runs a diff
sli diff -uc
```
```
# This command gets the device credentials from the default context, runs a diff and outputs the resulting diff in skillet format to the given filename.
sli diff -uc -o out.skillet.yaml -of skillet
```
```
# This command gets the device credentials from the default context, runs a diff and outputs the config diff between the running and candidate versions of your NGFW. The outputted diff is in set command format.
sli diff -uc -of set running candidate 
```
