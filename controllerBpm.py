from threading import Thread
import logging
import time
import os
import sys
import json
import queue

from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate
from datetime import datetime
# import managerBpm as manager


logger = logging.getLogger('rootlogger')

# BLE heart rate service
BLE_SERVICE_UUID ="00001810-0000-1000-8000-00805f9b34fb"
# Heart rate measurement that notifies.
BLE_CHARACTERISTIC_UUID= "00002a35-0000-1000-8000-00805f9b34fb"

class MyDelegate(btle.DefaultDelegate):
    def __init__(self, bp_dataHandler):
        btle.DefaultDelegate.__init__(self)
        self.bp_dataHandler = bp_dataHandler
        self.resetMeasure()

    def resetMeasure(self):
        print("Reset old_measure")
        self.old_measure = ''

    def handleNotification(self, cHandle, data):
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
            new_measure = f'{syst}{dias}{arte}{pulse}'
            self.bp_dataHandler.bpm_data = BpmDataInstance(
                                systolic=syst,
                                diastolic=dias,
                                arterial=arte,
                                pulse=pulse,
                            )
            self.old_measure = new_measure
        
        # sys.exit("received")
        # bpmController.start() # now able to create running loop that restarts after getting data once


class BpmDataInstance: # when instantiated, used to move data to json file
    def __init__(self, systolic, diastolic, arterial, pulse):
        print("Start BpmDataInstance init")

        # self.isStable = isStable | i think this Stable is specific to weighingscale right
        self.systolic = systolic
        self.diastolic = diastolic
        self.arterial = arterial
        self.pulse = pulse

        print("End BpmDataInstance init")

    def toJson(self):
        print("Start BpmDataInstance toJson")

        dataDictionary = {
            "systolic": self.systolic,
            "diastolic": self.diastolic,
            "arterial": self.arterial,
            "pulse": self.pulse
        }

        msg = json.dumps(dataDictionary)

        print(msg)

        print("End BpmDataInstance toJson")
        return msg


class BpmDataHandler(object): 
    def __init__(self):
        print("Start BpmDataHandler init")

        # i think it imports data from datainstance
        self._bpm_data = BpmDataInstance(
            systolic=0,
            diastolic=0,
            arterial=0,
            pulse=0
        )

        self._observers = []

        print("End BpmDataHandler init")

    @property
    def bpm_data(self):
        return self._bpm_data

    @bpm_data.setter
    def bpm_data(self, value):
        self._bpm_data = value
        print("Start observers loop")
        for callback in self._observers:
            print('Announcing change')
            callback(self._bpm_data)

    def bind_to(self, callback):
        print(f'Bound {callback}')
        self._observers.append(callback)


class ScanProcessor():
    def __init__(self, bp_dataHandler, mac):
        print("Start ScanProcessor init")

        self.bp_dataHandler = bp_dataHandler
        self.mac = mac
        self.scan_timeout = 5
        self.address = None
        self.resetMeasure()

        print("End ScanProcessor init")

    def resetMeasure(self):
        print("Reset old_measure")
        self.old_measure = ''

    def handleDiscovery(self, dev, isNewDev, isNewData):

        if not dev.addr == self.mac.lower():
            #logger.info('Unrecognized device')
            return
        
        print("Omron BPM found : " + dev.addr)
        while True: #dev.addr == self.mac.lower():
            # if dev.addr == self.mac.lower():
            # print("Omron BPM found : " + dev.addr)
            self.findBpm()
            # bpmController.start()
            # print("handle loop done")
            
            # x = 0
            # while True:
            #     x +=1
            #     print(x)
            #     time.sleep(2.0)

    def findBpm(self):
        print("Start BpmFinder findBpm")

        self.scanner = Scanner()
        devices = self.scanner.scan(self.scan_timeout)

        for dev in devices:
            if dev.addr == '28:ff:b2:2c:b9:af':
                print(f'THE BPM HAS BEEN FOUND: {dev.addr}')
                self.subscribe(dev.addr)
        return


    def subscribe(self, devaddr):         
        dev1 = btle.Peripheral(devaddr, btle.ADDR_TYPE_PUBLIC)
        dev1.setDelegate( MyDelegate(self.bp_dataHandler)) # change to withDelegate
        
        service_uuid = btle.UUID(BLE_SERVICE_UUID)
        ble_service = dev1.getServiceByUUID(service_uuid)

        char_uuid = btle.UUID(BLE_CHARACTERISTIC_UUID)
        data_chrc = ble_service.getCharacteristics(char_uuid)[0]
        chrc_hnd = data_chrc.getHandle()
        
        dev1.writeCharacteristic(chrc_hnd+1, b"\x02\x00", withResponse=True)
        print("Indications Enabled")

        # indication loop --------
        # while True:
        #maybe put a try somewhere in this loop 

        while True:
            if dev1.waitForNotifications(2.0):
        # handleNotification() was called
                continue
            return
            print("Waiting...")
        
        # bpmController.start()
        # maybe try putting an if connected kind of statement here to prevent getting stuck in this loop when disconnected
            # t._started.clear()
            # t.start()

            

class BpmController():
    def __init__(self):
        print("Start BpmController init")

        self.mac = None
        self.connected = False
        self.dataHandler = BpmDataHandler()
        self.q = None
        self.scanner = None
        self.stopped = False

        print("End BpmController init")

    def setMAC(self, mac):
        self.mac = mac

    def setQueue(self, queue):
        self.q = queue

    def update(self):
        try:
            while True:
                time.sleep(1)
                print("Controller update loop")

                if self.stopped:
                    print('Controller update stopped, breaking')
                    break

                self.scanner.scan(timeout=7)
        except Exception as e:
            print(f"{e}")
            raise

    def start(self):
        if not self.q:
            print('Unable to start without queue. Use setQueue(...)')
            return

        if not self.mac:
            print('Unable to start without mac. Use setMAC(...)')
            return

        print("Start BpmController start")

        self.scanProcessor = ScanProcessor(self.dataHandler, self.mac)
        self.dataHandler.bind_to(self.receiveBpmDataCallBack)
        

        print("Create Bluetooth Scanner")
        self.scanner = btle.Scanner().withDelegate(self.scanProcessor)
        # see what withDelegate function does exactly

        # global t 
        self.t = Thread(target=self.update, args=())
        self.t.start()

    def receiveBpmDataCallBack(self, data):
        ret = data.toJson()
        print(f"Receive Update For Handler: {ret}") #16/7: reached here, need to create a q with the manager to put. UPDATE 30/7- DONE
        self.q.put(ret)
        print(
            f'Added to queue. Approximate queue size: {self.q.qsize()}')

    def stop(self):
        print("Start BpmController stop")
        self.stopped = True
        self.__cleanUp()

    def __cleanUp(self):
        print("Start BpmController clean up")

        if self.t.is_alive():
            self.t.join()

# if __name__ == '__main__': # for testing this file individually
#     bpmController = BpmController()
#     bpmController.setMAC("28:ff:b2:2c:b9:af")
#     bpmController.setQueue(queue.Queue())
#     bpmController.start()

# bpmController = BpmController()
# bpmController.setMAC("28:ff:b2:2c:b9:af")
# bpmController.setQueue(queue.Queue())
# bpmController.start()

# TAKE NOTE OF THIS!!! - maybe consider it if threading still causing issues
# possible change to controller: 
# maybe keep the subscribing-to-indication part in another file, 
# and let the controller make reference to that file to keep everything in the same function


    # can consider some kinda "flag" coding:
    # set and manipulate some variables, use if statements to call the necessary loop functions and all that
    # can also try using the try except commands to wrap the calling of functions so that it's not always called?

    # maybe create another layer of function that calls the functions below that are needed to get the data (psuedo code by ding hao below)
    # def bpm_main(self):

        #check bluetooth state
        # check state
        # if not connected:
            # findbpm
            # while true ==
        # if connect