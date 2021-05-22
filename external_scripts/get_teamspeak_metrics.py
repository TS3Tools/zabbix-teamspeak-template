#!/usr/bin/python3
# About: Gathers some TeamSpeak server metrics.
# Author: Sebastian Krätzig <info@ts3-tools.info>

import sys
import re
import telnetlib
import string
import os.path
import xml.dom.minidom
import tempfile

# Import XML library with fallback to the original ElementTree
try:
  from lxml import etree
  #print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    #print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      #print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        #print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          #print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")
          sys.exit(1)

# Arguments
host = sys.argv[1]
query_port = sys.argv[2]
query_protocol = sys.argv[3]
query_user = sys.argv[4]
query_password = sys.argv[5]

# Temporary file to generate the gathered information to a XML file
xml_file_handler, xml_file_path = tempfile.mkstemp(suffix=".xml", prefix=None, dir=None, text=True)

# General helper variables
con_timeout = 5
command_expect_string = b"error id=0 msg=ok"

# raw specific variables
raw_expect_string = b"command."

# Establish a connection
# @par host:string IP address or DNS address of a TeamSpeak server
# @par query_port:number TCP port for the ServerQuery port
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @return: connection:object or error:string
def connect(host, query_port, query_protocol):
    if re.match('ssh', query_protocol, re.IGNORECASE):
        return "SSH!"

    elif re.match('raw', query_protocol, re.IGNORECASE):
        raw = telnetlib.Telnet()
        raw.open(host, query_port, con_timeout)
        raw.read_until(raw_expect_string)
        return raw

    else:
        print("Unsupported protocol '" + query_protocol + "'. Either use 'ssh' (secured) or 'raw' (telnet; deprecated).")
        sys.exit(1)

# Authenticate ServerQuery user
# @par connection:object Established ServerQuery connection
# @par query_user:string ServerQuery username (eg. 'serveradmin')
# @par query_password:string ServerQuery password
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @return: connection:object or error:string
def authenticate(connection, query_user, query_password, query_protocol):
    if re.match('ssh', query_protocol, re.IGNORECASE):
        return "SSH!"

    elif re.match('raw', query_protocol, re.IGNORECASE):
        command = bytes("login " + query_user + " " + query_password + "\n", encoding='utf-8')
        connection.write(command)
        connection.read_until(command_expect_string, con_timeout)
        return connection

    else:
        print("Unsupported protocol '" + query_protocol + "'. Either use 'ssh' (secured) or 'raw' (telnet; deprecated).")
        sys.exit(1)

# Execute ServerQuery command
# @par connection:object Established ServerQuery connection
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @par query_command:string ServerQuery command (eg. 'version')
# @return: decodedResponse:string or error:string
def execute_serverquery_command(connection, query_protocol, query_command, sid=None):
    if re.match('ssh', query_protocol, re.IGNORECASE):
        return "SSH!"

    elif re.match('raw', query_protocol, re.IGNORECASE):
        if sid != None:
            command = bytes("use sid=" + sid + "\n", encoding='utf-8')
            connection.write(command)
            connection.read_until(command_expect_string, con_timeout)

        command = bytes(query_command + "\n", encoding='utf-8')
        connection.write(command)
        response = connection.read_until(command_expect_string, con_timeout)
        return response[2:len(response)-19].decode('utf-8')

    else:
        print("Unsupported protocol '" + query_protocol + "'. Either use 'ssh' (secured) or 'raw' (telnet; deprecated).")
        sys.exit(1)

# Logout and close connection
# @par connection:object Established ServerQuery connection
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @return: decodedResponse:string or error:string
def disconnect(connection, query_protocol):
    if re.match('ssh', query_protocol, re.IGNORECASE):
        return "SSH!"

    elif re.match('raw', query_protocol, re.IGNORECASE):
        command = b"logout\n"
        connection.write(command)
        connection.read_until(command_expect_string, con_timeout)
        command = b"quit\n"
        connection.write(command)
        connection.read_until(command_expect_string, con_timeout)

    else:
        print("Unsupported protocol '" + query_protocol + "'. Either use 'ssh' (secured) or 'raw' (telnet; deprecated).")
        sys.exit(1)

# Function to replace teamspeak escape patterns
def unescape_string(escaped_string):
    unescaped_string = escaped_string.replace("\\\\", "\\") \
    .replace("\\/", "/") \
    .replace("\\s", " ") \
    .replace("\\p", "|")
    return unescaped_string

# Write data to XML file
# @par connection:object Established ServerQuery connection
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @par query_command:string ServerQuery command (eg. 'version')
# @return: decodedResponse:string or error:string
def writeToXml(command, data):
    # Append additional data to XML file, if it already exists
    # Else create a new XML file
    try:
        xml = etree.parse(xml_file_path)
        root = xml.getroot()
    except etree.ParseError:
        root = etree.Element("teamspeak-instance")

    # Split string of multiple key=value into single records
    if command == "bindinglist":
        data = data.split('|')

        # Binding list contains multiple non-unique keys 'ip'
        # Remove all 'ip' subelements and later insert the current values
        for parent in root.findall('.//ip/..'):
            for element in parent.findall('ip'):
                parent.remove(element)
    else:
        data = data.split(' ')

    for element in data:
        # Get key and value pair
        key = ''
        value = ''
        if '=' in element:
            key = element[element.find('_')+1:element.find('=')]
            value = unescape_string(element[element.find('=')+1: len(element)])
        else:
            key = element[element.find('_')+1:len(element)]

        # Generate XML structure
        # Each executed command has it's own XML element section, which contains the key=value pairs
        # <teamspeak-instance>
        #   <command1>
        #       <key1>value1</key1>
        #       <key2>value2</key2>
        #       <key3>value3</key3>
        #       [...]
        #   </command1>
        #   <command2>
        #       <key1>value1</key1>
        #       <key2>value2</key2>
        #       <key3>value3</key3>
        #       [...]
        #   </command2>
        # </teamspeak-instance>
        appendTo = root.find(command)
        if appendTo == None:
            appendTo = etree.SubElement(root, command)

        if command == "bindinglist":
            appendToSubElement = etree.SubElement(appendTo, key)
        else:
            appendToSubElement = appendTo.find(key)
            if appendToSubElement == None:
                appendToSubElement = etree.SubElement(appendTo, key)

        if value != '':
            appendToSubElement.text = value

    tree = etree.ElementTree(root)
    tree.write(xml_file_path, encoding="UTF-8", xml_declaration=True)

# Write data to XML file
# @par connection:object Established ServerQuery connection
# @par query_protocol:string ServerQuery Protocol ('ssh' or 'raw' (old, deprecated 'telnet'))
# @par query_command:string ServerQuery command (eg. 'version')
# @return: decodedResponse:string or error:string
def printXml():
    if os.path.isfile(xml_file_path):
        xmlFile = xml.dom.minidom.parse(xml_file_path)
        xmlPretty = xmlFile.toprettyxml()
    else:
        print("Could not find XML file")
        sys.exit(1)

    print(xmlPretty)

# Main function
def main():
    # Connect to ServerQuery interface
    connection = connect(host, query_port, query_protocol)
    # Authenticate ServerQuery user
    connection = authenticate(connection, query_user, query_password, query_protocol)

    # Gather version information
    # eg. version=3.13.3 build=1608128225 platform=Linux
    version = execute_serverquery_command(connection, query_protocol, "version")
    writeToXml("version", version)

    # Gather IP addresses used by the server instance
    # eg. ip=116.203.49.123|ip=2a01:4f8:c0c:ba03::1
    bindinglist = execute_serverquery_command(connection, query_protocol, "bindinglist")
    writeToXml("bindinglist", bindinglist)

    # Gather server instance properties
    # eg. serverinstance_database_version=34 serverinstance_filetransfer_port=30033 serverinstance_max_download_total_bandwidth=18446744073709551615 serverinstance_max_upload_total_bandwidth=18446744073709551615 serverinstance_guest_serverquery_group=1 serverinstance_serverquery_flood_commands=50 serverinstance_serverquery_flood_time=3 serverinstance_serverquery_ban_time=600 serverinstance_template_serveradmin_group=3 serverinstance_template_serverdefault_group=5 serverinstance_template_channeladmin_group=1 serverinstance_template_channeldefault_group=4 serverinstance_permissions_version=24 serverinstance_pending_connections_per_ip=0 serverinstance_serverquery_max_connections_per_ip=5
    instanceinfo = execute_serverquery_command(connection, query_protocol, "instanceinfo")
    writeToXml("instanceinfo", instanceinfo)

    # Gather server instance connection info
    # eg. instance_uptime=767925 host_timestamp_utc=1619474956 virtualservers_running_total=2 virtualservers_total_maxclients=40 virtualservers_total_clients_online=0 virtualservers_total_channels_online=68 connection_filetransfer_bandwidth_sent=0 connection_filetransfer_bandwidth_received=0 connection_filetransfer_bytes_sent_total=21624 connection_filetransfer_bytes_received_total=0 connection_packets_sent_total=12089147 connection_bytes_sent_total=1020743827 connection_packets_received_total=10111604 connection_bytes_received_total=861965773 connection_bandwidth_sent_last_second_total=0 connection_bandwidth_sent_last_minute_total=0 connection_bandwidth_received_last_second_total=0 connection_bandwidth_received_last_minute_total=0
    hostinfo = execute_serverquery_command(connection, query_protocol, "hostinfo")
    writeToXml("hostinfo", hostinfo)

    # Gather serverlist
    # eg. virtualserver_id=2 virtualserver_port=9987 virtualserver_status=online virtualserver_clientsonline=0 virtualserver_queryclientsonline=0 virtualserver_maxclients=30 virtualserver_uptime=768572 virtualserver_name=OCTA\seSports virtualserver_autostart=1 virtualserver_machine_id=1|virtualserver_id=4 virtualserver_port=9988 virtualserver_status=online virtualserver_clientsonline=0 virtualserver_queryclientsonline=0 virtualserver_maxclients=10 virtualserver_uptime=768572 virtualserver_name=4G-Server\s-\sDein\sPrepaid\sHoster\s😎 virtualserver_autostart=1 virtualserver_machine_id=1|virtualserver_id=5 virtualserver_port=9989 virtualserver_status=offline virtualserver_name=dat[sicknezz virtualserver_autostart=0 virtualserver_machine_id=1
    serverlist = execute_serverquery_command(connection, query_protocol, "serverlist")

    # Get some virtualserver counters
    virtualserver_total_counter = 0
    virtualserver_online_counter = 0
    virtualserver_offline_counter = 0
    virtualserver_clientsonline_counter = 0
    virtualserver_queryclientsonline_counter = 0

    # Split string of multiple key=value into single records
    serverlist = serverlist.split('|')
    for virtual_servers in serverlist:
        virtual_servers = virtual_servers.split(' ')

        for virtual_server in virtual_servers:
            key = virtual_server[virtual_server.find('_')+1:virtual_server.find('=')]
            value = unescape_string(virtual_server[virtual_server.find('=')+1: len(virtual_server)])

            if key == 'id':
                virtualserver_total_counter = virtualserver_total_counter + 1
            if key == 'status':
                if value == 'online':
                    virtualserver_online_counter = virtualserver_online_counter + 1
                else:
                    virtualserver_offline_counter = virtualserver_offline_counter + 1
            if key == 'clientsonline':
                virtualserver_clientsonline_counter = virtualserver_clientsonline_counter + int(value)
            if key == 'queryclientsonline':
                virtualserver_queryclientsonline_counter = virtualserver_queryclientsonline_counter + int(value)

    virtualserver_metrics = "virtualserver_total_counter=" + str(virtualserver_total_counter)
    virtualserver_metrics += " virtualserver_online_counter=" + str(virtualserver_online_counter)
    virtualserver_metrics += " virtualserver_offline_counter=" + str(virtualserver_offline_counter)
    virtualserver_metrics += " virtualserver_clientsonline_counter=" + str(virtualserver_clientsonline_counter)
    virtualserver_metrics += " virtualserver_queryclientsonline_counter=" + str(virtualserver_queryclientsonline_counter)
    writeToXml("virtualserver_metrics", virtualserver_metrics)

    # Disconnect and close session
    disconnect(connection, query_protocol)

    # Print XML, that Zabbix can parse it
    printXml()

# Call main and all sub-functions
main()
