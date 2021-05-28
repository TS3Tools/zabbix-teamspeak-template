# Zabbix TeamSpeak Template

[![CI](https://github.com/TS3Tools/zabbix-teamspeak-template/actions/workflows/github-ci-main.yml/badge.svg)](https://github.com/TS3Tools/zabbix-teamspeak-template/actions/workflows/github-ci-main.yml)

This repository allows you to monitor your TeamSpeak servers using Zabbix.

> "Zabbix is a mature and effortless enterprise-class open source monitoring solution for network monitoring and application monitoring of millions of metrics." - https://www.zabbix.com/

I would like to share this with you - the community - in order to further improve it together and build something great.

**Table of Contents**

- [Requirements](#requirements)
- [Supports](#supports)
- [Monitored Data](#monitored-data)
    - [Items](#items)
    - [Triggers](#triggers)
- [Installation](#installation)
    - [Install Python](#install-python)
    - [Configure sudo](#configure-sudo)
    - [User Parameters](#user-parameters)
    - [External Scripts](#external-scripts)
    - [Templates](#templates)
- [Configuration / Usage](#configuration-usage)
- [Available Macros](#available-macros)
- [How to contribute](#how-to-contribute)
- [Contributors](#contributors)
- [Donations](#donations)

## Requirements

- Zabbix server (version 5.0 or 5.2)
- Linux based TeamSpeak server (version 3.0 or newer)
- Linux package `sudo` on the Linux host, where the TeamSpeak server is running on

## Supports

- ServerQuery protocol `raw` (telnet)

## Monitored Data

### Items

The template is fetching a lot of information. For the full list, please check the template by your own.

Below some interesting items:

- TS3 Instance Platform (eg. `Linux`)
- TS3 Instance Build (eg. `1608128225`)
- TS3 Instance Version (eg. `3.13.3`)
- TS3 Instance Uptime (eg. `100 days, 10:20:21`)
- TS3 Latest Available Version (eg. `3.13.5`)
- TS3 Clients online (eg. `61` Clients)
- TS3 Instance Database Version (eg. `34`)
- TS3 Instance Permissions Version (eg. `24`)
- TS3 Instance ServerQuery Port reachable (eg. `Up (1)`)
- TS3 License Type (eg. `Activation License`)
- TS3 License Max. Slots (eg. `512`)
- TS3 License Max. Virtual Servers (eg. `10`)
- TS3 License Expiry Datetime (eg. `Thu Jul 22 00:00:00 2021`)
- TS3 Virtual Server (total) (eg. `9` Virtual Servers)
- TS3 Virtual Server (online) (eg. `7` Virtual Servers)
- TS3 Virtual Server (offline) (eg. `2` Virtual Servers)
- TS3 Process ID (PID) active (eg. `1`)

### Triggers

The template contains multiple triggers in order to alert in case of issues. For the full list, please check the template by your.

Below some interesting trigger examples:

- TS3 Instance has been restarted
- TS3 Instance has been crashed
- TS3 Instance ServerQuery port is unreachable
- TS3 Instance version changed (3.13.3 => 3.13.5)
- TS3 Instance reaches usage of max. slots (>80 %)
- TS3 Instance is not on the latest version
- TS3 Instance Flood Time of 300 is too high

## Installation

This section guides you through the installation of this template.

### Install Python

The Python script, which you will later install on the Zabbix server requires Python 3.

Please install the respective Linux package:

```shell
# Example for Debian
apt-get update
apt-get install python3
```

### Configure sudo

The Python script is executing some shell commands, which require root permissions. Due to this, these commands are being executed using `sudo`.

Please install the respective Linux package:

```shell
# Example for Debian
apt-get update
apt-get install sudo
```

Next, allow the Zabbix user to execute the required commands by the Python script. You can manage this in a dedicated sudoers file for example: `/etc/sudoers.d/99-zabbix-user`

```shell
# Required for UserParameters teamspeak
zabbix ALL=(root) NOPASSWD: /usr/bin/kill -0 *
zabbix ALL=(root) NOPASSWD: /usr/bin/du -sb *
```

PS: You might also want to add `zabbix ALL=(root) NOPASSWD: /usr/bin/nmap` to this file to allow Zabbix to run the script **Detect operating system** from the web interface. ;)

### User Parameters

This template also gathers some information using the active Zabbix agent. Therefore, you need to configure the required **User Parameters** on the host, where the Zabbix agent should execute some shell commands. The required user parameters by this template can be found in the [`zabbix_agentd.d/`](zabbix_agentd.d/) folder.

1. Connect using SSH to your host, where your TeamSpeak server is running on
2. Identify the path of your `Include` folder: `grep -Ei "^Include" /etc/zabbix/zabbix_agentd.conf`
3. Install all user parameters from the [`zabbix_agentd.d/`](zabbix_agentd.d/) folder into your user parameter (`Include`) folder (default: `/etc/zabbix/zabbix_agentd.d/`)
    ```shell
    cd /etc/zabbix/zabbix_agentd.d/
    wget https://raw.githubusercontent.com/TS3Tools/zabbix-teamspeak-template/main/zabbix_agentd.d/userparameter_teamspeak.conf
    wget https://raw.githubusercontent.com/TS3Tools/zabbix-teamspeak-template/main/zabbix_agentd.d/teamspeak_get_converted_license_end_date.sh
    ```
4. Ensure, that the permissions of these scripts are set correctly
    ```shell
    chown root:root -R /etc/zabbix/zabbix_agentd.d/
    chmod 644 /etc/zabbix/zabbix_agentd.d/*.conf
    chmod 755 /etc/zabbix/zabbix_agentd.d/*.sh
    ```
5. Restart the Zabbix agent to load the configuration of these new user parameters
    ```shell
    sudo systemctl restart zabbix-agent.service
    ```

### External Scripts

First of all, you need to install all external scripts, which are used by this template. Those can be found in the [`external_scripts/`](external_scripts/) folder.

1. Connect using SSH to your Zabbix monitoring server
2. Identify the path of your `ExternalScripts` folder: `grep -Ei "^externalscript" /etc/zabbix/zabbix_server.conf`
3. Install all scripts from the [`external_scripts/`](external_scripts/) folder into your `ExternalScripts` folder (default: `/usr/lib/zabbix/externalscripts`)
    ```shell
    cd /usr/lib/zabbix/externalscripts/
    wget https://raw.githubusercontent.com/TS3Tools/zabbix-teamspeak-template/main/external_scripts/get_teamspeak_metrics.py
    ```
4. Ensure, that the permissions of these scripts are set correctly
    ```shell
    chown root:root -R /usr/lib/zabbix/externalscripts/
    chmod 755 /usr/lib/zabbix/externalscripts/*
    ```

### Templates

Next, import all Zabbix [`templates/`](templates/):

1. Login with administrative permissions to your Zabbix server web interface
2. Go to **Configuration** -> **Templates**
3. Click on **Import**
4. Select the template from this repository
5. Mark the required options in import rules
6. Confirm the import by clicking on **Import**

For further information, you might want to take a look at the official Zabbix documentation: https://www.zabbix.com/documentation/current/manual/xml_export_import/templates

## Configuration / Usage

Now, you can start monitoring your TeamSpeak servers.

1. Login with administrative permissions to your Zabbix server web interface
2. Go to **Configuration** -> **Hosts**
3. Add a new host by clicking on **Create host** or edit an existing host by clicking on the hosts name
4. Open the tab **Templates**
5. In the field **Link new templates** enter **teamspeak** and select the template **Template App TeamSpeak 3**
6. Click on **Update** in order to assign this template to the host
7. Open the tab **Macros**
8. Add the required macros by the template with their respective values (see next section for available macros)
9. Click on **Update** to save the configured macros

Now, your TeamSpeak server should be already monitored. Verify this by checking the latest monitoring data:

1. Login with administrative permissions to your Zabbix server web interface
2. Go to **Monitoring** -> **Latest data**
3. Select or enter **TeamSpeak 3 Server** as **Application**
4. Click on **Apply** to see all available data for this specific application

**Note:** The item **TS3 Full XML** will be always empty as it only contains the XML data from the Python script, parses it and immediately discards it afterwards.

After a few minutes should have some monitoring data like the **TS3 Instance Version**, **TS3 Instance Uptime** or **TS3 License Expiry Datetime**.

## Available Macros

**Hint:** Currently, the Python script `get_teamspeak_metrics.py` does only support the `raw` protocol for the connection. Support for `ssh` is prepared, but not implemented yet.

Macro                       | Default Value   | Description
:-------------------------- | :-------------- | :-------------
{$TS3_INSTANCE_HOME_DIR}    | /home/teamspeak | The root directory, where the TeamSpeak server is installed. The `ts3server_startscript.sh` should be located there.
{$TS3_QUERY_IP}             | 127.0.0.1       | The IP address, which is listening for the ServerQuery interface.
{$TS3_QUERY_PORT}           | 10011           | The port, which is listening for the ServerQuery interface.
{$TS3_QUERY_PROTOCOL}       | raw             | The protocol, which should be used by the ServerQuery commands. Possible values: `raw` (telnet; unsecure), `ssh` (ssh; encrypted)
{$TS3_QUERY_USER}           | serveradmin     | The ServerQuery user, which is allowed to gather all information.
{$TS3_QUERY_PASSWORD}       | *empty*         | The password of the previous configured ServerQuery user.

## How to contribute

Any improvements to the Zabbix TeamSpeak monitoring template are welcome. Simply create a merge request with your improvements.

## Contributors

[Open list of contributors](graphs/contributors)

## Donations

**Zabbix TeamSpeak Template** is free software and is made available free of charge. Your donation, which is purely optional, supports me at improving the software as well as reducing my costs of this project. If you like the software, please consider a donation. Thank you very much!

[Donate with PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7ZRXLSC2UBVWE)
