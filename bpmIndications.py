# This code is intended to run on a device with up to date Bluez.
# Works on Raspberry Pi or Mac.
# Currently configured to stream heart rate.
# https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.service.heart_rate.xml
# Bluepy Docs
# @see http://ianharvey.github.io/bluepy-doc/
#  Notifciations doc: 
# @see http://ianharvey.github.io/bluepy-doc/notifications.html
# Code assumes adapter is already enabled, and scan was already done.

from bluepy import btle
# from btle import ADDR_TYPE_PUBLIC
import time
import binascii
from struct import unpack
import sys


# Address of BLE device to connect to.
BLE_ADDRESS = "28:ff:b2:2c:b9:af"
# BLE heart rate service
BLE_SERVICE_UUID ="00001810-0000-1000-8000-00805f9b34fb"
# Heart rate measurement that notifies.
BLE_CHARACTERISTIC_UUID= "00002a35-0000-1000-8000-00805f9b34fb"
#Descriptor to subscribe to for indications
# BLE_DESCRIPTOR= "00002902-0000-1000-8000-00805f9b34fb"

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        # ... initialise here

    def handleNotification(self, cHandle, data):
        # print(data)
        if cHandle == 2065:
            syst = data[1]
            dias = data[3]
            arte = data[5]
            pulse = data[14]
            print("Systolic Pressure = %s mmHg" % syst)
            print("Diastolic Pressure = %s mmHg" % dias)
            print("Pulse Rate = %s" % pulse)
            print("Arterial Pressure = %s mmHg" % arte)
            yearBytes = str(data[7:9])
            yearString = yearBytes[8:10] + yearBytes[4:6]
            year = int(yearString, 16)
            print("Date & time = %s/%s/%s , %s:%s:%s" % (data[10], data[9], year, data[11], data[12], data[13]))
        sys.exit("Data received")
        return


# class scanProcessor2():
#     def __init__(self):
#         print("scan processor here")

#     def handleDiscovery(self, dev):
#         if dev.addr == self.mac.lower():
#             print("OMRON BPM FOUND")
#             for (sdid, _, data) in dev.getScanData():
#                 print(f'sdid: {sdid}, desc: {data}')

#     def start(self):
        

print("Connecting...")
dev = btle.Peripheral(BLE_ADDRESS, btle.ADDR_TYPE_PUBLIC)
print("peripheral set")
print(dev)
# dev.setMTU(512)
dev.setDelegate( MyDelegate() )
print("delegate set")

# print(dev.getState())

service_uuid = btle.UUID(BLE_SERVICE_UUID)
ble_service = dev.getServiceByUUID(service_uuid)
print("service identified")

char_uuid = btle.UUID(BLE_CHARACTERISTIC_UUID)
data_chrc = ble_service.getCharacteristics(char_uuid)[0]
print(data_chrc)
# NOTE : data_chrc.supportsRead() = false


#handles are displayed in output in decimal form. 2a35 handle = 0x0811 = 2065
chrc_hnd = data_chrc.getHandle()
# chrc_hnd1 = chrc_hnd+1
# chrc_hnd1 = data_chrc.getHandle() + 1
# print(chrc_hnd1)
# print(chrc_hnd1)


# NOTE: maybe try to make more sense of the nrf connect logs
# and see how they are getting the data from the 2a35


# print "Debug Services..."
# for svc in dev.services:
# 	print str(svc)

# print 'Debug Characteristics...'
# for ch in ble_service.getCharacteristics():
#     print str(ch)

# print 'Debug Descriptors...'
# for dsc in dev.getDescriptors():
#     print str(dsc) + str() + str( dsc.uuid)

# Enable the sensor, start notifications
# Writing x01 is the protocol for all BLE notifications.

dev.writeCharacteristic(chrc_hnd+1, b"\x02\x00", withResponse=True)
# dev.writeCharacteristic(0x0811, b"\x01\x00")

# dev.writeCharacteristic(chrc_hnd+1, b"\x02\x00", withResponse=True)
# dev.writeCharacteristic(chrc_hnd, b"\x02\x00")

# NOTE : 2a35 characteristic unable to be read

# desc_uuid = btle.UUID(BLE_DESCRIPTOR)
# data_desc = data_chrc.getDescriptors(desc_uuid)[0]
# print(data_desc)


# data_desc.write(b"\x02\x00", withResponse=True)
# data_chrc.write(b"\x01\x00")
print("Indications Enabled")

# time.sleep(1.0) # Allow sensor to stabilise

# Main loop --------
while True:
    if dev.waitForNotifications(2.0):
        # handleNotification() was called
        continue
    print("Waiting...")