# Shelly Repo

## Shelly Plus 1
 
In this section you will find information about the [Shelly Plus 1](https://shelly.cloud/shelly-plus-1/)

### DISCLAIMER (progress at own risk! I can't be liable for any damage you do to the device!)

### Bluetooth Low-Energy (BLE)
The Shelly 1 plus has Bluetooth Low-Energy functionality (BLE). It would seem that this is used to configure the Shelly device (set Wifi. etc) as well as query it (e.g.,get settings) via the application. When BLE is used the communications can be sniffed easily using a Nordic nRF52840-Dongle, so keep that in mind if you use BLE.

#### How to talk to Shelly Plus 1 via BLE
WARNING: IT IS POSSIBLE TO SNIFF BLE WHICH IS IN CLEAR TEXT (Authentication implementation doesn't protect against this, so make use of a complicated and long Shelly Authentication Password.)

Make sure you turn ```off Bluetooth``` if you are not using it or at least ```enable Authentication```.

The developers make use of JSON over BLE to communicate with the device. This is the same JSON used by the Web App (any payload sent to the RPC system can be used via Bluetooth). The list below is just a sample of what can be done.

Feel free to clone the repo. and contribute to the list.

It is possible to communicate with the device via BLE and the following GATT characteristic UUIDs:

```
UUID_RW          = "5F6D4F53-5F52-5043-5F64-6174615F5F5F"
UUID_READ_NOTIFY = "5F6D4F53-5F52-5043-5F72-785F63746C5F"
UUID_W           = "5F6D4F53-5F52-5043-5F74-785F63746C5F"
```

Due to the size of JSON we need to tell the device how much data to expect. This is done by sending to ```UUID_W``` the length (little-endian) of the JSON message to be sent to ```UUID_RW```.

Then it is possible to send a message to ```UUID_RW``` for processing. If there is a reply, the requesting client needs to get the size of the reply. This can be found by querying ```UUID_READ_NOTIFY```. Based on it's size (buffer limit is 254 bytes) the script would need to make further queries to retrieve the remaining data.

Example:

To send the following query (length: 43 bytes (```0x2B```)):
```{"id":1641784978,"method":"Wifi.GetStatus"}```

Send ```'\x00\x00\x00\x2B'``` to GATT: ```UUID_W``` 

Next, send ```{"id":1641784978,"method":"Wifi.GetStatus"}``` to GATT: ```UUID_RW``` 

Read the GATT ```UUID_READ_NOTIFY``` for the length of the reply sent in ```UUID_RW```. Read ```UUID_RW``` till message is complete (value of length from ```UUID_READ_NOTIFY```). 

```UUID_READ_NOTIFY``` came back with ```'\x00\x00\x00x'``` which is ``120`` decimal. (Less than 254 so one read is enough.)

Reading ```UUID_RW``` gives ```{"id":1641784978,"src":"shellyplus1-XXXXXXXXXXXX","result":{"sta_ip":null,"status":"disconnected","ssid":null,"rssi":0}}```

#### JSON Schema and Format


|method|Description| Command example | Example Result | 
|---|---|---|---|
|"Shelly.GetDeviceInfo"| Returns source (shelly ID), shelly mac address, model string, generation, firmware id, version, app, if auth is enabled and authentication domain (unauthenticated)| ```{"id":1641784978,"method":"Shelly.GetDeviceInfo"}``` | ```{"id":1641784978,"src":"shellyplus1-XXXXXXXXXXXX","result":{"id":"shellyplus1-XXXXXXXXXXXX", "mac":"XXXXXXXXXXXX", "model":"SNSW-00xxxx", "gen":2, "fw_id":"20210x/X.X.", "ver":"0.X.0", "app":"Plus1", "auth_en":false,"auth_domain":null}}``` |
|"Shelly.GetStatus"|Returns Shelly details |```{"id":1641784978,"method":"Shelly.GetStatus"}``` | ```{"id":1641784978,"src":"shellyplus1-XXXXXXXXXXXX","result":{"ble":{},"cloud":{"connected":false},"input:0":{"id":0,"state":false},"mqtt":{"connected":false},"switch:0":{"id": 0, "source": "init", "output": false,"temperature":{"tC":57.1, "tF":134.8}},"sys":{"mac":"XXXXXXXXXXXX","restart_required":false,"time":"0x:29","unixtime":1641784978,"uptime":62,"ram_size":264304,"ram_free":163148,"fs_size":414401,"fs_free":266813,"available_updates":{"beta":{"version":"0.x.x-beta2"},"stable":{"version":"0.x.x"}}},"wifi":{"sta_ip":"x.x.x.x","status":"got ip","ssid":"SSID","rssi":-x8}}}``` |
|"Wifi.GetStatus"|Returns source (shelly ID), standalone ip address, if it is connected, the ssid it is connected to and the Wifi signal strength (RSSI)|```{"id":1641784978,"method":"Wifi.GetStatus"}``` | ```{"id":1641784978,"src":"shellyplus1-XXXXXXXXXXXX","result":{"sta_ip":null,"status":"disconnected","ssid":null,"rssi":0}}``` status: "connecting","disconnected", "got ip" | 
|"Sys.Reboot"| Reboots the Shelly (authentication needed?) | ``` {"id":1641784978,"method":"Sys.Reboot" }```| reboots system|
|"Shelly.Reboot"| Reboots the Shelly  | ``` {"id":1641784978,"method":"Shelly.Reboot" }```| reboots system|
|"Ble.SetConfig"| Disable BLE  | ``` {"id":1641784978,"method":"Ble.SetConfig", "params":{"config": {"enable": false} } }``` | none | 
|"WiFi.SetConfig"| Set the Wifi Settings, ```sta``` is Wifi 1 and ```sta1``` is Wifi 2 | ``` {"id":1641784978,"method":"WiFi.SetConfig","src":"shelly-app", "params":{"config": {"sta2":{ "enable": true,"ssid":"SSID_HERE","pass":"PASS_HERE","sta_ip":"10.0.0.1","roam_interval": 900}} }``` | On success nothing is returned, otherwise detailed error message | 
|"switch.set"|Turn off or on the switch |```{"id":"1641784978","src":"shelly-app","method":"switch.set","params":{"id":0,"on":false}}``` or ```{"id":"1641784978","src":"shelly-app","method":"switch.set","params":{"id":0,"on":true}}```|```{"id":"1641784978","src":"shellyplus1-XXXXXXXXXXXX","dst":"shelly-app","result":{"was_on":true}} ```|

Shelly JSON Schema for a Query:

```
{
  "type":"object",
  "properties":{
    "id":{
      "description": "A unique identifier for the query (*nix time)",
      "type":"number",
      "required":true
    },
    "method":{
      "type":"string",
      "required":true
    },
    "params":{
      "type":"object"
    },
    "src":{
      "type":"string"
    }
}    
```

### Authentication

The Shelly device uses a SHA256 hashing function to generate a hashed response. It uses a number of inputs (nonce, unixtime, etc.) and a shared secret (authentication password) as an authentication method (see example Python code).

Make sure you sent a complicated and secure password as communications can be sniffed (BLE) and the password could be easily brute-forced offline.

```
from time import mktime
from datetime import datetime
from hashlib import sha256
	
def auth(password, realm, nonce, nc):
        current_time = int(time.time())
        dummy_method = "dummy_method"
        dummy_uri = "dummy_uri"
        cat =sha256("admin:" + realm + ":" + password).hexdigest()
        rat =sha256(dummy_method + ":" + dummy_uri).hexdigest()
        lat = cat + ":" + str(nonce) + ":" + str(nc) + ":" + str(current_time) + ":auth:" + rat
        data =sha256(lat).hexdigest()
        return data, current_time
```

Get an error response from the server to get the required inputs, nonce, realm, nc and algorithm:

```
{"id":1641784978,"src":"shellyplus1-111111111111","error":{"code":401,"message":"{"auth_type": "digest", "nonce": 1641861674, "nc": 1, "realm": "shellyplus1-111111111111", "algorithm": "SHA-256"}"}} 
```

The command would then include the following:

```
{"id":"1641784978","method":"shelly.getconfig", "auth":{"realm":"shellyplus1-111111111111","username":"admin","nonce":1641861674,"cnonce":1641950701,"response":"922e52ec8855052c97507f812e97a3d1f473d3be6697fff18f789152f42cbc55","algorithm":"SHA-256"}
```

### Python Script - shelly-ble.py

The script I provide makes use of the ```bleak``` and ```construct``` Python libraries. Check the [requirements.txt](requirements.txt) file.

### How to get started:

```
$ git clone https://github.com/epicRE/shelly-smart-device
$ cd shelly-smart-device
$ virtualenv pyenv
$ source pyenv/bin/activate
(pyenv)$ pip3 install -r requirements.txt
(pyenv)$ python3 shelly-ble.py

```
Scan mode (when ```get_device = True```, this is the default initial state of the script)

```
[**] Shelly Plus 1 BLE Script by KXynos (2022)
[+] Running scan
Address: Description
xxxx-xxx-xxx-xxxx-xxxxx: ShellyPlus1-xxxxxxxxxxx
```

Open ```shelly-ble.py``` with your favourit editor and paste this value ```XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX``` into the variable ```address```. Look for the ShellyPlus1-xxxxxxxxxxx string at the end of the each line; this is the device name(address)(ini MS Windows it will have a different format) and serial number (you can match it with the one on the device). Also set ```get_device = False``` (we don't need it anymore, you might need it again if you change devices or get another one).

Run the script a second time:

```
(pyenv)$ python3 shelly-ble.py
```
