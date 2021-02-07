import esp_at_uart
from machine import Pin
import utime as time

TEST_AP_SSID = "YOUR_AP_SSID"
TEST_AP_PASS = "YOUR_AP_PWD"

esp = esp_at_uart.ESPCHIP(1, 9600)

# indicate program started visually
led_onboard = Pin(25, Pin.OUT)
led_onboard.value(0)     # onboard LED OFF for 0.5 sec
time.sleep(0.5)
led_onboard.value(1)

print('Testing Generic Methods')
print('=======================')

print('AT startup...')
if esp.test():
    print('Success!')
else:
    print('Failed!')

# esp.uart_cfg_def()
# esp.factory_reset()

# print('Soft-Reset...')
# if esp.reset():
#    print('Success!')
# else:
#    print('Failed!')

print('Another AT startup...')
if esp.test():
    print('Success!')
else:
    print('Failed!')

print('Version...')
if esp.version(debug=True):
       print('Success!')
else:
   print('Failed!')

print()

print('Testing WIFI Methods')
print('====================')

wifi_mode = "STATION"
print("Testing get_mode/set_mode of value '%s'(%i)..." %
      (wifi_mode, esp_at_uart.WIFI_MODES[wifi_mode]))
esp.set_mode(esp_at_uart.WIFI_MODES[wifi_mode])
if esp.get_mode() == esp_at_uart.WIFI_MODES[wifi_mode]:
    print('Success!')
else:
    print('Failed!')

print('Connecting WLAN...')
if esp.connect(TEST_AP_SSID, TEST_AP_PASS, debug=False):
    print('Success!')
else:
    print('Failed!')

print('Checking if connected WLAN %s' % (TEST_AP_SSID))
ret = esp.get_accesspoint()
if ret and ret.get('ssid') == TEST_AP_SSID:
    print('Success!')
else:
    print('Failed!')

print('Disconnecting from WLAN...')
if esp.disconnect():
    print('Success!')
else:
    print('Failed!')

print('Checking if not connected WLAN...')
if esp.get_accesspoint() == None:
    print('Success!')
else:
    print('Failed!')

print('Setting Station mode...')
if esp.set_mode(esp_at_uart.WIFI_MODES['STATION']):
    print('Failed!')
else:
    print('Success!')

print('Scanning for WLANs...')
wlans = esp.list_all_accesspoints(timeout=20000, debug=False)
print(wlans)
# for wlan in wlans:
#     print("Scanning for WLAN '%s'..." % (wlan['ssid']))
#     for wlan2 in esp.list_accesspoints(wlan['ssid']):
#         print(wlan2)

print('Setting AP + Station mode...')
if esp.set_mode(esp_at_uart.WIFI_MODES['SOFTAP_STATION'], debug=False):
    print('Failed!')
else:
    print('Success!')

print('Reading access point configuration')
print(esp.get_accesspoint_config())
print('Listing all stations connected to the module in access point mode...')
print(esp.list_stations())

print('Read DHCP client and server settings:')
dhcpCfg = esp.get_dhcp_config()
print(dhcpCfg)

print('Checking DHCP client and server settings...')
if not dhcpCfg["station"]:
    print('    Enable Station DHCP...')
    esp.set_dhcp_config(1, True)
else:
    print('    Disable Station DHCP & Setting static IP...')
    esp.set_station_ip('192.168.0.10')
    esp.set_dhcp_config(1, False)
if not dhcpCfg["softAP"]:
    print('    Enable SoftAP DHCP...')
    esp.set_dhcp_config(2, True)
else:
    print('    Disable SoftAP DHCP & Setting static IP...')
    esp.set_accesspoint_ip('192.168.4.1')
    esp.set_dhcp_config(2, False)

print('Setting autoconnect to access point in station mode...')
esp.set_autoconnect(True)
esp.set_autoconnect(False)
esp.set_autoconnect(True)

print('Reading the station IP...')
print(esp.get_station_ip())

print('Reading the access point IP...')
print(esp.get_accesspoint_ip())
