#!/usr/bin/env python3
# 
# Description: Shelly Plus 1 - BLE remote query script
# 
# Author: Konstantinos Xynos (2022)
# How to: 
#  Script assumes Authentication is disabled on the Shelly. It won't work otherwise. 
#  Set get_device = True and run the script. Get the address (look for a name ShellyPlus1-XXXXXXXXXXXXX) 
#   and add it to the ADDRESS variable
#  Set get_device = False and run the script again.  
#  The script will issue two commands: "Shelly.GetDeviceInfo" and "Wifi.GetStatus" which are both 
#   only informative and make no changes to the device.
#
# WARNING: USE THIS SCRIPT AND KNOWLEDGE AT YOUR OWN RISK. IT IS 
# POSSIBLE TO CAUSE ISSUES WITH YOUR DEVICE IF YOU TRANSMIT 
# INCORRECT CODES/COMMANDS AND DATA TO IT. 
# YOU ACCEPT FULL RESPONSILIBITY RUNNING THIS SCRIPT AND/OR ITS CONTENTS
#

import asyncio
from bleak import BleakClient, discover
from construct import BytesInteger
from datetime import datetime
import logging
import time

ADDRESS = "" # EDIT THIS 

UUID_RW              = "5F6D4F53-5F52-5043-5F64-6174615F5F5F"
UUID_READ_NOTIFY     = "5F6D4F53-5F52-5043-5F72-785F63746C5F"
UUID_W               = "5F6D4F53-5F52-5043-5F74-785F63746C5F"

async def run_ble_client(address: str, char_uuid_rw: str, char_uuid_readout: str,char_uuid_write: str, queue: asyncio.Queue):
    
    async def request_data(client,char_uuid_rw,char_uuid_write, request_data):
        await client.write_gatt_char(char_uuid_write, BytesInteger(4).build(len(request_data)))
        await asyncio.sleep(1.0)
        await client.write_gatt_char(char_uuid_rw, request_data)
        logging.info(f"Client Request (length: {len(request_data)}): {request_data.decode()}")
        
        result = await client.read_gatt_char(char_uuid_readout)
        result_int = BytesInteger(4).parse(result)
        await asyncio.sleep(1.0)
        logging.info(f"Client notify (bytearray, int): {result}, {result_int}")
        count = 0
        result = ''
        while(count < result_int):
            await asyncio.sleep(1.0)
            result_ = await client.read_gatt_char(char_uuid_rw)
            count = count + len(result_)
            result = result + result_.decode()
        logging.info(f"Client Result : {result} ")
            
    async with BleakClient(address) as client:
        logging.info(f"Connected: {client.is_connected}")
        await request_data(client,char_uuid_rw,char_uuid_write, b'{"id":1641784978,"method":"Shelly.GetDeviceInfo"}')
        await request_data(client,char_uuid_rw,char_uuid_write, b'{"id":1641784978,"method":"Wifi.GetStatus"}')
        # Send an "exit command to the consumer"
        await queue.put((time.time(), None))

async def main(address: str, char_uuid_rw: str,char_uuid_readout: str,char_uuid_write: str):
    now = datetime.now()
 
    if address == '':
        print("[!] Device address not set. Try scanning using get_device = True ")
        exit(-1)

    queue = asyncio.Queue()
    client_task = run_ble_client(address, char_uuid_rw, char_uuid_readout, char_uuid_write, queue)
    
    await asyncio.gather(client_task)
    logging.info("Main method done.")

def scan_for_devices():
    # EDIT THIS
    # Use True to get the address for your ShellyPlus1-XXXXXXXXXXXXX
    get_device = True # can be True or False  

    if get_device:
        async def run():
            devices = await discover()
            print("[+] Running scan")
            print("Address: Description")
            for d in devices:
                print(d)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
        print("[*] Copy your device's address (e.g.named ShellyPlus1-xxx..) and set it in the variable address.")
        print("[!] Please accept liability. By changing the flag and executing this script you accept full responsilibity of what might happpen to your device.")
        print("[!] Don't forget to set, get_device = False ")
        print("[!] EOF ")

        exit(1)
def printHi():
    print("[**] Shelly Plus 1 BLE Script by K.Xynos (2022) [**]")

if __name__ == "__main__":
    printHi()
    scan_for_devices()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(ADDRESS,UUID_RW,UUID_READ_NOTIFY,UUID_W))
