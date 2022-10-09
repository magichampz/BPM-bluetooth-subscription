# BPM-bluetooth-subscription

Running controllerBpm will run an endless loop searching for an Omron BPM that satisfies the specified MAC address. Only when the BPM enters pairing mode, which is either after a reading on when you press the pairing mode button, will the controllerBpm locate, connect to and subscribe to the BPM to recieve indications containing the blood pressure data.

To test it out first, run bpmIndications when your Omron BPM is already in paring mode to enable your Raspberry Pi to subscribe to bluetooth messages (indcations) from your OMRON Blood Pressure Monitor. Before that, please ensure that you have enabled your Pi to access these indications by giving it the correct authentication. You can check out this thread for more information on how to do that: https://stackoverflow.com/questions/62147384/raspberry-ble-encryption-pairing?rq=1

