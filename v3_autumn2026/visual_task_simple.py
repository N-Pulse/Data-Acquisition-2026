# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 14:45:53 2023

@author: gwenael.birot
"""


from psychopy import core
import serial # install pyserial library to use serial


class Trigger:
    def __init__(self, source=None, port='LPT1', duration=0.01):
        self._source = source
        self._port = port
        self._duration = duration

        if source == 'arduino':
            self._device = serial.Serial(self._port,baudrate=115200)
            print(self._device.name)         # check which port was really used
            self._device.write((0).to_bytes(1,byteorder='big'))
        elif source == 'LPT':
            parallel.setPortAddress(port)
            parallel.setData(0)

        core.wait(0.1)

    def setData(self,value):
        if self._source is None:
            pass
        elif self._source == 'LPT':
            parallel.setData(value)
            core.wait(self._duration,0.01)
            parallel.setData(0)
        elif self._source == 'arduino':
            self._device.write(value.to_bytes(1,byteorder='big'))
            core.wait(self._duration,0.01)
            self._device.write((0).to_bytes(1,byteorder='big'))

        #print(clock.getTime())


    def close(self):
        if self._source is None:
            pass
        elif self._source == 'LPT':
            pass
        elif self._source == 'arduino':
            self._device.close()


if __name__ == "__main__":
    win.callOnFlip(trigger.setData,triggerValue[n%2])
