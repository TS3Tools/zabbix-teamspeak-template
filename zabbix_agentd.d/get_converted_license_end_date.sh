#!/usr/bin/env bash
# About: Gets the TeamSpeak license expiry date and converts it to a Unix timestamp.
# Author: Sebastian Krätzig <sebastian.kraetzig@ts3-tools.info>
# Source: https://github.com/TS3Tools/zabbix-teamspeak-template

TEAMSPEAK_ROOT_DIR=${1}

IFS=' ' read -r -a LICENSE_END_DATE_ARRAY <<< $(grep -Ei '^end date' ${TEAMSPEAK_ROOT_DIR}/licensekey.dat | cut -d ':' -f 2- | xargs)

date -d "${LICENSE_END_DATE_ARRAY[2]} ${LICENSE_END_DATE_ARRAY[1]} ${LICENSE_END_DATE_ARRAY[4]} ${LICENSE_END_DATE_ARRAY[3]}" +"%s" -u | xargs
