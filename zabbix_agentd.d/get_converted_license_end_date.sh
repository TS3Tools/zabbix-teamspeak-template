#!/usr/bin/env bash
# About: Gets the TeamSpeak license expiry date and converts it to a Unix timestamp.
# Author: Sebastian Krätzig <sebastian.kraetzig@ts3-tools.info>
# Source: https://github.com/TS3Tools/zabbix-teamspeak-template

TEAMSPEAK_ROOT_DIR=${1}
TEAMSPEAK_LICENSE_FILE="${TEAMSPEAK_ROOT_DIR}/licensekey.dat"

if [[ -f "${TEAMSPEAK_LICENSE_FILE}" ]]; then
    IFS=' ' read -r -a LICENSE_END_DATE_ARRAY <<< "$(grep -Ei '^end date' ${TEAMSPEAK_LICENSE_FILE} 2> /dev/null | cut -d ':' -f 2- | xargs)"

    date -d "${LICENSE_END_DATE_ARRAY[2]} ${LICENSE_END_DATE_ARRAY[1]} ${LICENSE_END_DATE_ARRAY[4]} ${LICENSE_END_DATE_ARRAY[3]}" +"%s" -u | xargs
else
    # Max. Unix timestamp for "no license", which has no expiry date
    echo 2147483647
fi
