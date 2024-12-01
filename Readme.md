# Venus Kostal Plenticore plugin

This plugin obtains the current production from an kostal plenticore (or similar) inverter and displays it in venus os.
The data is used to calculated the internal consumption, etc. and is also included in the VRM graphs.

## Kompatibility

This plugin should work with all PIKO IQ and PLENTICORE PLUS inverters. Go to `http://your-inverters-ip/api/v1/info/version`, if you get a response like this:   
```
{
  "sw_version": "01.15.04581",
  "api_version": "0.2.0",
  "name": "PUCK RESTful API",
  "hostname": "scb"
}
```
you might be lucky and this plugin works for you. If you're interested in the api itself, have a look at the inverters swagger UI for api documentation at `http://your-inverters-ip/api/v1`. 
If you happen to have another api version and this script does not work anymore - let me know.
If you don't get an response - this plugin won't help you and you should search further ;) 

## Inspiration/code sources:
- https://github.com/schenlap/venus_kostal_pico Thanks to schenlap for his plugin for the (original) pico inverters. I've used his code and ideas on the dbus side to get the data into venus os
- https://github.com/RalfZim/venus.dbus-fronius-smartmeter Thanks to ralfzim for his service configuration 
- https://stackoverflow.com/questions/59053539/api-call-portation-from-java-to-python-kostal-plenticore-inverter thanks to E3EAT for the session token calculation 

## Requirements: 
This plugin does only work on Venus os **LARGE** - so if you're running the 'normal' version make sure to upgrade first

Background (only if you want to know why): For session initialization this script requires AES from the pycryptodomex lib. Pycryptodomex needs gcc and stdlibs during it's installation, these seem to be available on the large venus version, but not on the normal. If you know how to get pycryptodomex installed on normal venus os versions let me know!

## Installation

Connect via ssh as root to your venus os. If you don't have root access jet, see here: https://www.victronenergy.com/live/ccgx:root_access

### Install dependencies:
Important: You might need to reinstall these dependencies after a venus os update to get the plugin running again as the update seems to overwride everything outside the /data dir)

1. install pip (python package manager): run `opkg update` and `opkg install python3-pip`
2. install pycryptodomex `pip3 install pycryptodomex`

### Install plugin:

Download all files from this repo and copy them to the new dir `/data/venus_kostal_plenticore`.
If you download the code as .zip from github, make sure to remove the `-main` prefix. 
Create that dir if it does not jet exists. 
Venus OS does not come with git, so I recommend cloning/downloading this repo to your machine, then transfer all files e.g. using scp (`scp -r venus_kostal_plenticore/* root@venusip:/data/venus_kostal_plenticore/`)


### Configure plugin:

1. configure `kostal.ini`: set kostal_name, the inverters ip, the vrm instance, password and refresh interval. 
    ```
    [kostal_name]
    ip = http://192.168.178.XXX
    instance = 50
    password = XXX
    interval = 5
    position = 0 # 0:AC input 1, 1: AC output, 2: AC input 2
    ``` 

2. set File permissions for run and kill scripts:
   - `chmod 755 /data/venus_kostal_plenticore/service/run`
   - `chmod 744 /data/venus_kostal_plenticore/kill_me.sh`

   
3. Verify that your setup is correct:

   - Run `/data/venus_kostal_plenticore/kostal.py /data/venus_kostal_plenticore/kostal.ini`. If everything works fine you should see your kostals current values printed periodically. If not fix your config/installation and try again.

4. Enable services:
   - `ln -s /data/venus_kostal_plenticore/service /service/venus_kostal_plenticore` The daemon-tools should automatically start this service within seconds.

5. Configure this script to start when venus OS is booted:
   Create rc.local, make it executable:
   ```
   echo -e '#!/bin/bash' >> /data/rc.local
   echo 'ln -s /data/venus_kostal_plenticore/service /service/venus_kostal_plenticore' >> /data/rc.local
   chmod +x /data/rc.local 
   ```   
   If you already have the file `/data/rc.local` only add the line  `ln -s /data/venus_kostal_plenticore/service /service/venus_kostal_plenticore` to it.
   The rc.local file is executed when venus os boots and will create the link in the service directory for you


### What to do if you have multiple plenticores? 

If you have multiple plenticores, you have to create a service for each one. So duplicate the service dir (`/data/venus_kostal_plenticore/service`) to e.g. `/data/venus_kostal_plenticore/service-east-roof` and `/data/venus_kostal_plenticore/service-west-roof`.
Also duplicate the config and edit the run scripts in both service folders so that both use their own config.
Make sure that all kostals have different instance values, otherwise only one will show up in the gui-v2.
Lastly link both services in the /service dir as shown in step 5.
Make sure that you configure different names for both inverters.






