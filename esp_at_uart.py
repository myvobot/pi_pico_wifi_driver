from machine import UART
import utime as time

# This hashmap collects all generic AT commands
CMDS_GENERIC = {
    'TEST_AT': b'AT',
    'RESET': b'AT+RST',
    'VERSION_INFO': b'AT+GMR',
    'DEEP_SLEEP': b'AT+GSLP',
    'ECHO': b'ATE',
    'FACTORY_RESET': b'AT+RESTORE',
    'UART_CFG_DEF': b'AT+UART_DEF=9600,8,1,0,0'
}

# All WIFI related AT commands
CMDS_WIFI = {
    'MODE': b'AT+CWMODE',
    'CONNECT': b'AT+CWJAP',
    'LIST_APS': b'AT+CWLAP',
    'DISCONNECT': b'AT+CWQAP',
    'AP_SET_PARAMS': b'AT+CWSAP',
    'AP_LIST_STATIONS': b'AT+CWLIF',
    'DHCP_CONFIG': b'AT+CWDHCP',
    'SET_AUTOCONNECT': b'AT+CWAUTOCONN',
    'SET_STATION_MAC': b'AT+CIPSTAMAC',
    'SET_AP_MAC': b'AT+CIPAPMAC',
    'SET_STATION_IP': b'AT+CIPSTA',
    'SET_AP_IP': b'AT+CIPAP'
}

# IP networking related AT commands
CMDS_IP = {
    'STATUS': b'AT+CIPSTATUS',
    'START': b'AT+CIPSTART',
    'SEND': b'AT+CIPSEND',
    'CLOSE': b'AT+CIPCLOSE',
    'GET_LOCAL_IP': b'AT+CIFSR',
    'SET_MUX_MODE': b'AT+CIPMUX',
    'CONFIG_SERVER': b'AT+CIPSERVER',
    'SET_TX_MODE': b'AT+CIPMODE',
    'SET_TCP_SERVER_TIMEOUT': b'AT+CIPSTO',
    'UPGRADE': b'AT+CIUPDATE',
    'PING': b'AT+PING'
}

# HTTP Client related AT commands
CMDS_HTTP = {
    'HTTP_CLIENT': b'AT+HTTPCLIENT'
}

HTTP_METHODS = {
    "HEAD": 1,
    "GET": 2,
    "POST": 3,
    "PUT": 4,
    "DELETE": 5,
}

# data type of HTTP client request.
CONTENT_TYPES = {
    "application/x-www-form-urlencoded": 0,
    "application/json": 1,
    "multipart/form-data": 2,
    "text/xml": 3,
}

# WIFI network modes the ESPCHIP knows to handle
WIFI_MODES = {
    'STATION': 1,
    'SOFTAP': 2,
    'SOFTAP_STATION': 3,
}
VALID_WIFI_MODES = list(WIFI_MODES.values())

# WIFI network security protocols known to the ESPCHIP module
WIFI_ENCRYPTION_PROTOCOLS = {
    'OPEN': 0,
    'WEP' : 1,
    'WPA_PSK': 2,
    'WPA2_PSK': 3,
    'WPA_WPA2_PSK': 4,
    'WPA2_ENTERPRISE': 5,
    'WPA3_PSK': 6,
    'WPA2_WPA3_PSK': 7
}
VALID_WIFI_ENCRYPTION_PROTOCOLS = list(WIFI_ENCRYPTION_PROTOCOLS.values())

class CommandError(Exception):
    pass


class CommandFailure(Exception):
    pass


class UnknownWIFIModeError(Exception):
    pass

class InvalidParameterError(Exception):
    pass

class ESPCHIP(object):

    def __init__(self, uart=1, baud_rate=115200):
        """Initialize this module. uart may be an integer or an instance
        of machine.UART. baud_rate can be used to set the Baud rate for the
        serial communication."""
        if uart:
            if type(uart) is int:
                # self.uart = UART(uart, baud_rate)
                from uart_timeout_any import uartTimeOut
                self.uart = uartTimeOut(uart, baud_rate)
            elif type(uart) is UART:
                self.uart = uart
            else:
                raise Exception(
                    "Argument 'uart' must be an integer or machine.UART object!")
            print(self.uart)
        else:
            raise Exception("Argument uart must not be 'None'!")

    def _send_command(self, cmd, timeout=0, debug=False):
        """Send a command to the ESPCHIP module over UART and return the
        output.
        After sending the command there is a 1 second timeout while
        waiting for an answer on UART. For long running commands (like AP
        scans) there is an additional N seconds grace period to return
        results over UART.
        Raises an CommandError if an error occurs and an CommandFailure
        if a command fails to execute."""
        if debug:
            start = time.ticks_ms()
        cmd_output = []
        okay = False
        if cmd == '' or cmd == b'':
            raise CommandError("Unknown command '" + cmd + "'!")

        # AT commands must be finalized with an '\r\n'
        cmd += '\r\n'
        if debug:
            print("%8i - TX: %s" %
                  (time.ticks_diff(time.ticks_ms(), start), str(cmd)))
        self.uart.write(cmd)

        # wait at maximum one second for a command reaction
        cmd_timeout = 100
        while cmd_timeout > 0:
            if self.uart.any():
                cmd_output.append(self.uart.readline())
                if debug:
                    print("%8i - RX: %s" %
                          (time.ticks_diff(time.ticks_ms(), start), str(cmd_output[-1])))
                if cmd_output[-1].rstrip() == b'OK':
                    if debug:
                        print("%8i - 'OK' received!" %
                              (time.ticks_diff(time.ticks_ms(), start)))
                    okay = True
            else:
                time.sleep_ms(10)
            cmd_timeout -= 1
        if cmd_timeout == 0 and len(cmd_output) == 0:
            if debug == True:
                print("%8i - RX timeout of answer after sending AT command!" %
                      (time.ticks_diff(time.ticks_ms(), start)))
            else:
                print("RX timeout of answer after sending AT command!")

        # read output if present
        while self.uart.any():
            cmd_output.append(self.uart.readline())
            if debug:
                print("%8i - RX: %s" %
                      (time.ticks_diff(time.ticks_ms(), start), str(cmd_output[-1])))
            if cmd_output[-1].rstrip() == b'OK':
                if debug:
                    print("%8i - 'OK' received!" %
                          (time.ticks_diff(time.ticks_ms(), start)))
                okay = True

        # handle output of AT command
        if len(cmd_output) > 0:
            if cmd_output[-1].rstrip() == b'ERROR':
                raise CommandError('Command error!')
            elif cmd_output[-1].rstrip() == b'OK':
                okay = True
            elif not okay:
                # some long running commands do not return OK in case of success
                # and/or take some time to yield all output.
                if timeout == 0:
                    cmd_timeout = 500
                else:
                    if debug:
                        print("%8i - Using RX timeout of %i ms" %
                              (time.ticks_diff(time.ticks_ms(), start), timeout))
                    cmd_timeout = timeout / 10
                while cmd_timeout > 0:
                    if self.uart.any():
                        cmd_output.append(self.uart.readline())
                        if debug:
                            print("%8i - RX: %s" %
                                  (time.ticks_diff(time.ticks_ms(), start), str(cmd_output[-1])))
                        if cmd_output[-1].rstrip() == b'OK':
                            okay = True
                            break
                        elif cmd_output[-1].rstrip() == b'FAIL':
                            raise CommandFailure()
                    else:
                        time.sleep_ms(10)
                    cmd_timeout -= 1
            if not okay and cmd_timeout == 0 and debug:
                print("%8i - RX-Timeout occured and no 'OK' received!" %
                      (time.ticks_diff(time.ticks_ms(), start)))
        return cmd_output

    @classmethod
    def _join_args(cls, *args, debug=False):
        """Joins all given arguments as the ESPCHIP needs them for the
        argument string in a 'set' type command.
        Strings must be quoted using '"' and no spaces outside of quoted
        srrings are allowed."""
        while type(args[0]) is tuple:
            if len(args) == 1:
                args = args[0]
        if debug:
            print(args)
        str_args = []
        for arg in args:
            if type(arg) is str:
                str_args.append('"' + arg + '"')
            elif type(arg) is bytes:
                str_args.append(arg.decode())
            elif type(arg) is bool:
                str_args.append(str(int(arg)))
            elif arg is not None:
                str_args.append(str(arg))
        if debug:
            print(str_args)
        return ','.join(str_args).encode()

    @classmethod
    def _parse_accesspoint_str(cls, ap_str):
        """Parse an accesspoint string description into a hashmap
        containing its parameters. Returns None if string could not be
        split into 3 or 5 fields."""
        if type(ap_str) is str:
            ap_str = ap_str.encode()
        ap_params = ap_str.split(b',')
        if len(ap_params) == 5:
            (enc_mode, ssid, rssi, mac, channel) = ap_params
            ap = {
                'encryption_protocol': int(enc_mode),
                'ssid': ssid,
                'rssi': int(rssi),
                'mac': mac,
                'channel': int(channel)
            }
        elif len(ap_params) == 3:
            (enc_mode, ssid, rssi) = ap_params
            ap = {
                'encryption_protocol': int(enc_mode),
                'ssid': ssid,
                'rssi': int(rssi),
            }
        else:
            ap = None
        return ap

    def _query_command(self, cmd, timeout=0, debug=False):
        """Sends a 'query' type command and return the relevant output
        line, containing the queried parameter."""
        return self._send_command(cmd + b'?', timeout=timeout, debug=debug)[1].rstrip()

    def _set_command(self, cmd, *args, timeout=0, debug=False):
        """Send a 'set' type command and return all lines of the output
        which are not command echo and status codes.
        This type of AT command usually does not return output except
        the echo and 'OK' or 'ERROR'. These are not returned by this
        method. So usually the result of this method must be an empty list!"""
        return self._send_command(cmd + b'=' + ESPCHIP._join_args(args, debug=debug), timeout=timeout, debug=debug)[1:-2]

    def _execute_command(self, cmd, timeout=0, debug=False):
        """Send an 'execute' type command and return all lines of the
        output which are not command echo and status codes."""
        return self._send_command(cmd, timeout=timeout, debug=debug)[1:-2]

    def test(self, debug=False):
        """Test the AT command interface."""
        return self._execute_command(CMDS_GENERIC['TEST_AT'], debug=debug) == []

    def version(self, debug=False):
        """Read the version."""
        return self._execute_command(CMDS_GENERIC['VERSION_INFO'], debug=debug) is not None

    def factory_reset(self, debug=False):
        return self._execute_command(CMDS_GENERIC['FACTORY_RESET'], debug=debug)[-1] == b'OK'

    def uart_cfg_def(self, debug=False):
        self._execute_command(CMDS_GENERIC['UART_CFG_DEF'], debug=debug)

    def reset(self, debug=False):
        """Reset the module and read the boot message.
        """
        boot_log = []
        if debug:
            start = time.ticks_ms()
        self._execute_command(CMDS_GENERIC['RESET'], debug=debug)

        # wait for module to boot and messages appearing on self.uart
        timeout = 500
        while not self.uart.any() and timeout > 0:
            time.sleep_ms(10)
            timeout -= 1
        if debug and timeout == 0:
            print("%8i - RX timeout occured!" %
                  (time.ticks_diff(time.ticks_ms(), start)))

        # wait for messages to finish
        timeout = 300
        while timeout > 0:
            if self.uart.any():
                boot_log.append(self.uart.readline())
                if debug:
                    print("%8i - RX: %s" %
                          (time.ticks_diff(time.ticks_ms(), start), str(boot_log[-1])))
            time.sleep_ms(20)
            timeout -= 1
        if debug and timeout == 0:
            print("%8i - RTimeout occured while waiting for module to boot!" %
                  (time.ticks_diff(time.ticks_ms(), start)))
        if not boot_log:
            return False
        return boot_log[-1].rstrip() == b'ready'

    def get_mode(self, debug=False):
        """Returns the mode the ESP WIFI is in:
            1: station mode
            2: accesspoint mode
            3: accesspoint and station mode
        Check the hashmap WIFI_MODES for a name lookup.
        Raises an UnknownWIFIModeError if the mode was not a valid or
        unknown.
        """
        mode = int(self._query_command(
            CMDS_WIFI['MODE'], debug=debug).split(b':')[1])
        if mode in VALID_WIFI_MODES:
            return mode
        else:
            raise UnknownWIFIModeError("Mode '%d' not known!" % mode)

    def set_mode(self, mode, debug=False):
        """Set the given WIFI mode.
        Raises UnknownWIFIModeError in case of unknown mode."""
        if mode not in VALID_WIFI_MODES:
            raise UnknownWIFIModeError("Mode '%d' not known!" % mode)
        return self._set_command(CMDS_WIFI['MODE'], mode, debug=debug)

    def get_accesspoint(self, debug=False):
        """ Read the SSID of the currently joined access point.
        The SSID 'No AP' tells us that we are not connected to an access
        point! """
        answer = self._query_command(CMDS_WIFI["CONNECT"], debug=debug)
        # print("AP: " + str(answer))
        result = None
        if answer and answer != b'No AP':
            ret = answer.split(b'+' + CMDS_WIFI['CONNECT'][3:] + b':')[1]
            r = ret.split(b',')
            # print(r)
            if len(r) >= 8:
                result = {
                    "ssid": r[0].strip(b'"').decode('utf-8'),
                    "bssid": r[1].strip(b'"').decode('utf-8'),
                    "channel": int(r[2]),
                    "rssi": int(r[3]),
                    "pciEn": int(r[4]),
                    "reconnInterval": int(r[5]),
                    "listenInterval": int(r[6]),
                    "scanMode": int(r[7]),
                }
        return result

    def connect(self, ssid, psk, debug=False):
        """Tries to connect to a WIFI network using the given SSID and
        pre shared key (PSK). Uses a 20 second timeout for the connect
        command.
        """
        ret = self._set_command(CMDS_WIFI['CONNECT'], ssid,
                          psk, debug=debug, timeout=20000)
        if ret and len(ret):
            return ret[-1] == b'WIFI GOT IP\r\n'
        else:
            return False

    def disconnect(self, debug=False):
        """Tries to connect to a WIFI network using the given SSID and
        pre shared key (PSK)."""
        return self._execute_command(CMDS_WIFI['DISCONNECT'], debug=debug) == []

    @classmethod
    def _parse_list_ap_results(cls, ap_scan_results):
        aps = []
        for ap in ap_scan_results:
            try:
                ap_str = ap.rstrip().split(
                    CMDS_WIFI['LIST_APS'][-4:] + b':')[1].decode()[1:-1]
            except IndexError:
                # Catching this exception means the line in scan result
                # was probably rubbish
                continue
            # parsing the ap_str may not work because of rubbish strings
            # returned from the AT command. None is returned in this case.
            ap = ESPCHIP._parse_accesspoint_str(ap_str)
            if ap:
                aps.append(ap)
        return aps

    def list_all_accesspoints(self, timeout=10000, debug=False):
        """ List all available access points.
        """
        return ESPCHIP._parse_list_ap_results(self._execute_command(CMDS_WIFI['LIST_APS'], timeout=timeout, debug=debug))

    def list_accesspoints(self, *args):
        """List accesspoint matching the parameters given by the
        argument list.
        The arguments may be of the types string or integer. Strings can
        describe MAC adddresses or SSIDs while the integers refer to
        channel names."""
        return ESPCHIP._parse_list_ap_results(self._set_command(CMDS_WIFI['LIST_APS'], args))

    def set_accesspoint_config(self, ssid, password, channel, encrypt_proto, debug=False):
        """Configure the parameters for the accesspoint mode. The module
        must be in access point mode for this to work.
        After setting the parameters the module is reset to
        activate them.
        The password must be at least 8 characters long up to a maximum of
        64 characters.
        WEP is not allowed to be an encryption protocol.
        Raises CommandFailure in case the WIFI mode is not set to mode 2
        (access point) or 3 (access point and station) or the WIFI
        parameters are not valid."""
        if self.get_mode(debug=False) not in (2, 3):
            raise CommandFailure('WIFI not set to an access point mode!')
        if type(ssid) is not str:
            raise CommandFailure('SSID must be of type str!')
        if type(password) is not str:
            raise CommandFailure('Password must be of type str!')
        if len(password) > 64 or len(password) < 8:
            raise CommandFailure('Wrong password length (8..64)!')
        if channel not in range(1, 15) and type(channel) is not int:
            raise CommandFailure('Invalid WIFI channel!')
        if encrypt_proto not in (0, 2, 3, 4) or type(encrypt_proto) is not int:
            raise CommandFailure('Invalid encryption protocol!')
        self._set_command(CMDS_WIFI['AP_SET_PARAMS'], ssid,
                          password, channel, encrypt_proto, debug=debug)
        self.reset()

    def get_accesspoint_config(self, debug=False):
        """ Reads the current access point configuration. The module must
        be in an acces point mode to work.
        Returns a hashmap containing the access point parameters.
        Raises CommandFailure in case of wrong WIFI mode set. """
        if self.get_mode(debug=debug) not in (2, 3):
            raise CommandFailure('WIFI not set to the access point mode!')
        ret = self._query_command(CMDS_WIFI['AP_SET_PARAMS'], debug=debug)
        (ssid, password, channel, encryption_protocol, max_conn, ssid_hidden) = \
            ret.split(b':')[1].split(b',')
        return {
            'ssid': ssid,
            'password': password,
            'channel': int(channel),
            'encryption_protocol': int(encryption_protocol),
            'max_conn': int(max_conn),
            'ssid_hidden': int(ssid_hidden)
        }

    def list_stations(self, debug=False):
        """List IPs of stations which are connected to the access point.
        ToDo: Parse result and return python list of IPs (as str)."""
        return self._execute_command(CMDS_WIFI['AP_LIST_STATIONS'], debug=debug)

    def get_dhcp_config(self, debug=False):
        ret = self._query_command(CMDS_WIFI['DHCP_CONFIG'], debug=debug)
        state = int(ret.split(b':')[1])
        return {
            "station": True if state & 0x01 else False,
            "softAP": True if state & 0x02 else False,
        }

    def set_dhcp_config(self, mode, operate, debug=False):
        """Set the DHCP configuration for a specific mode.
        <operate>:
        0: disable
        1: enable
        <mode>:
        Bit0: Station DHCP
        Bit1: SoftAP DHCP
        """
        return self._set_command(CMDS_WIFI['DHCP_CONFIG'], int(operate), mode, debug=debug)

    def set_autoconnect(self, autoconnect, debug=False):
        """Set if the module should connnect to an access point on
        startup."""
        return self._set_command(CMDS_WIFI['SET_AUTOCONNECT'], autoconnect, debug=debug)

    def get_station_ip(self, debug=False):
        """get the IP address of the module in station mode.
        The IP address must be given as a string. No check on the
        correctness of the IP address is made."""
        return self._query_command(CMDS_WIFI['SET_STATION_IP'], debug=debug)

    def set_station_ip(self, ip_str, debug=False):
        """Set the IP address of the module in station mode.
        The IP address must be given as a string. No check on the
        correctness of the IP address is made."""
        return self._set_command(CMDS_WIFI['SET_STATION_IP'], ip_str, debug=debug)

    def get_accesspoint_ip(self, debug=False):
        """get the IP address of the module in access point mode.
        The IP address must be given as a string. No check on the
        correctness of the IP address is made."""
        return self._query_command(CMDS_WIFI['SET_AP_IP'], debug=debug)

    def set_accesspoint_ip(self, ip_str, debug=False):
        """Set the IP address of the module in access point mode.
        The IP address must be given as a string. No check on the
        correctness of the IP address is made."""
        return self._set_command(CMDS_WIFI['SET_AP_IP'], ip_str, debug=debug)

    def get_connection_status(self):
        """Get connection information.
        ToDo: Parse returned data and return python data structure."""
        return self._execute_command(CMDS_IP['STATUS'])

    def start_connection(self, protocol, dest_ip, dest_port, debug=False):
        """Start a TCP or UDP connection.
        ToDo: Implement MUX mode. Currently only single connection mode is
        supported!"""
        self._set_command(CMDS_IP['START'], protocol,
                          dest_ip, dest_port, debug=debug)

    def send(self, data, debug=False):
        """Send data over the current connection."""
        self._set_command(CMDS_IP['SEND'], len(data), debug=debug)
        print(b'>' + data)
        self.uart.write(data)

    def ping(self, destination, debug=False):
        """Ping the destination address or hostname."""
        return self._set_command(CMDS_IP['PING'], destination, debug=debug)

    def http_request(self, url, data=None, headers=[], method="GET", contentType="application/x-www-form-urlencoded", debug=False):
        """Connect to a webpage URL and download html content.
        """
        if method not in HTTP_METHODS:
            raise InvalidParameterError('Unknown http method')
        if contentType not in CONTENT_TYPES:
            raise InvalidParameterError('Unknown content Type')

        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""
        path = "/" + path
        if proto == "http:":
            transportType = 1 # HTTP_TRANSPORT_OVER_TCP
            port = 80
        elif proto == "https:":
            transportType = 2 # HTTP_TRANSPORT_OVER_SSL
            port = 443
        else:
            raise InvalidParameterError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        res = self._set_command(CMDS_HTTP['HTTP_CLIENT'],
                        HTTP_METHODS[method],
                        CONTENT_TYPES[contentType],
                        url,
                        host,
                        path,
                        transportType,
                        data,
                        # TODO: multiple headers
                        debug=debug)
        # print(res)
        l = 0
        rdata = b''
        magic = b'+' + CMDS_HTTP['HTTP_CLIENT'][3:] + b':'
        if res and len(res):
            for line in res:
                if line.startswith(magic):
                    x = line.split(magic)
                    if len(x) > 1:
                        _pos = x[1].find(b',')
                        l += int(x[1][0 : _pos])
                        rdata += x[1][_pos+1:]
                else:
                    rdata += line
                    if len(rdata) > l:
                        rdata = rdata[:l] # ignore the last \r\n
        return {"size": l, "data": rdata }
