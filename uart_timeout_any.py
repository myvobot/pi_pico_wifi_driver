from machine import UART
import utime

"""
The MicroPython port for Pi Pico has no timeout for readline() at this moment.
We use this hack to make sure it won't get stuck forever.
"""

class uartTimeOut(UART):

   def readline(self, timeOut=100):
       if timeOut is None:
           return super().readline()
       else:
           now = utime.ticks_ms()
           data = b''
           while True:
               if utime.ticks_ms()-now > timeOut:
                   break
               else:
                   if super().any():
                       _d = super().read(1)
                       data += _d
                       if "\n" in _d:
                           break
           return data
