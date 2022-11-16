"""boardmon
Communications monitor.
"""

import serial
import time

# Keep reading from serial line until full prompt is seen


class Comm:
    """wrapper for communications interface
    """

    def __init__(self, port, prompt=">>> ", icpause=None, baudrate=115200):
        """Initialize with:
        port - serial communication port, e.g., "COM3"
        prompt - match prompt, e.g., "Fusethat >>>"; default is ">>>"
        icpause - inter-character pause in seconds
        """
        self.port = port
        self.prompt = prompt
        self.icpause = icpause
        self.baudrate = baudrate
        self.cooked = None              # processed response
        self.raw = None                 # unprocessed response
        self.handle = None
        try:
            self.handle = serial.Serial(port, baudrate, timeout=60)
        except serial.SerialException:
            print("Error: cannot open", port)
            raise IOError("cannot open " + port)

    def send(self, cm):
        """Send a command line 'cm' to serial port and await prescribed prompt.
        """
        if cm[-1] != '\r':
            cm += '\r'

        if not self.icpause:
            byteseq = cm.encode('utf-8')    # convert to ASCII/UTF-8
            self.handle.write(byteseq)      # send to port
        else:
            for bb in cm:
                bytes = bb.encode('utf-8')
                self.handle.write(bytes)
                time.sleep(self.icpause)
        self.raw = ""
        self.cooked = ""
        while True:
            b = self.handle.read(1)
            if len(b) == 0:
                # We can only get here due to timeout
                # print("Could not find prompt; so far read:")
                # print(s)
                return 1

            c = b.decode('utf-8')
            self.raw += c
            if self.raw.endswith(self.prompt):
                # ok = True
                # print(self.raw)
                self.cooked = self.raw.lower()
                return 0

    def response(self):
        """Get respond from last command.
        """
        return self.cooked
