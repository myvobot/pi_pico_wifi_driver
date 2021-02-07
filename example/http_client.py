import esp_at_uart

# Note: AT http is only available on ESP32/ESP32-S2 AT firmware.

TEST_AP_SSID = "YOUR_AP_SSID"
TEST_AP_PASS = "YOUR_AP_PWD"

esp = esp_at_uart.ESPCHIP(1, 9600)

def connect(ssid, pwd):
    esp.set_mode(esp_at_uart.WIFI_MODES["STATION"])
    if not esp.get_mode() == esp_at_uart.WIFI_MODES["STATION"]:
        return False

    print('Connecting WLAN...')
    return esp.connect(ssid, pwd)

def run():
    print('Start')
    if esp.test():
        print('Ready')
        ok = connect(TEST_AP_SSID, TEST_AP_PASS)
        if ok:
            print('Connected:', esp.get_station_ip())
            res = esp.http_request("http://httpbin.org/get", debug=False)
            print('Received: ', res['size'], 'bytes')
            print('Body:')
            print(res['data'].decode('utf-8'))
        else:
            print('WiFi Failed')
    else:
        print('AT Failed!')

run()
