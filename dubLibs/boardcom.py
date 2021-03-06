"""
boardcom: Board Communications
Implemented as a class providing access to:
send(command)
resp = response()
"""

import sys
import time
import serial
from serial.tools.list_ports import comports
from tkinter.messagebox import askretrycancel


# Keep reading from serial line until full prompt is seen
class BoardComm:
    """wrapper for communications interface
    """

    def __init__(self, prompt=">>>", icpause=None, baudrate=115200):
        """Initialize with:
        port - serial communication port, e.g., "COM3"
        prompt - match prompt, e.g., "Fusethat >>>"; default is ">>>"
        icpause - inter-character pause in seconds
        """
        self.port = None
        self.prompt = prompt
        self.icpause = icpause
        self.baudrate = baudrate
        self.cmdline = None
        self.cooked = None              # processed response
        self.raw = None                 # unprocessed response
        self.handle = None

        # additional attributes
        self.vrfyout = sys.stdout       # default verify-out
        self.vrfyprogress = False       # default verify report progress

    def getPortList(self):
        portList = []
        ports = serial.tools.list_ports.comports()
        for i in range(len(ports)):
            if ports[i].manufacturer == 'FTDI':  # find ports made by 'FTDI'
                portList.append(ports[i].device)
        return portList

    def findPorts(self):
        portList = self.getPortList()
        while portList == []:
            if askretrycancel('Connection Error', 'Connect a COM port. Retry?'):
                portList = self.getPortList()
            else:
                sys.exit
                break
        portList.sort()  # in-place sorting of the list
        return portList  # return sorted port list

    def connect(self, comport):
        try:
            self.handle = serial.Serial(comport, self.baudrate, timeout=60)
            # print(self.handle)
        except serial.SerialException:
            print("Error: cannot open", comport)
            raise IOError("cannot open " + comport)

        print('Port: %s' % comport)
        return self.handle
        # return comport

    def disconnect(self, comport):
        if comport:
            self.handle.close()
            # print(self.handle)

    def autoConnect(self, defaultPort):
        portList = self.find_ports()
        if portList:
            port = portList[0]
            self.connect(port)

    def send(self, cm):
        """Send a command line 'cm' to serial port and await prescribed prompt.
        """
        self.cmdline = cm
        # print("SEND", cm)        # uncomment for low level command debugging
        if cm[-1] != '\r':
            cm += '\r'

        if not self.icpause:
            byteseq = cm.encode('utf-8')  # convert to ASCII/UTF-8
            self.handle.write(byteseq)  # send to port
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
                #print("Could not find prompt; so far read:")
                # print(s)
                return 1

            c = b.decode('utf-8')
            self.raw += c
            #print("bm raw", self.raw)
            if self.raw.endswith(self.prompt):
                #ok = True
                # print(self.raw)
                self.cooked = self.raw.lower()
                #print ("cooked:", self.cooked)
                return 0

    def set_vrfy_attrs(self, vrfyout=None, vrfyprogress=None):
        """Set 'sendvrfy' attributes
        vrfyout : file stream for command output
        vrfyprogress : report progress when done
        """
        # This probably would be keyword recognition
        if vrfyout:
            self.vrfyout = vrfyout
        if vrfyprogress:
            self.vrfyprogress = vrfyprogress

    # def sendvrfy(self, cm, annotation=None, showout=False, reflines=None):

    def sendvrfy(self, cm, annotation=None, reflines=None):
        """Send a command 'cm' and optionally verify result via 'assert'.
        This method produces text 
        If annotation not provided, 'assert' will use 'cm'.
        If 'progress' is True, inform when done.

        """
        vout = self.vrfyout     # verify-out stream
        self.send(cm)
        resp = self.response()
        if annotation is None:
            annotation = cm

        # verify successful completion of command
        assert resp.endswith(self.prompt), annotation
        if self.vrfyprogress:
            print(" .", annotation, "done", file=vout)
        resplines = self.responselines()
        if reflines:
            matched = True
            for ref, got in zip(reflines, resplines):
                assert ref == got, annotation
                if ref != got:
                    matched = False
                    break
            if not matched:
                matched = False

            return matched
        else:
            return True

    def response(self):
        """Get respond from last command.
        """
        return self.cooked

    def responselines(self):
        """Return raw response as list of lines.
        Excludes original command and prompt after command.
        """
        resplines = []
        for line in self.raw.splitlines():
            resplines.append(line.strip())
        if resplines[0] == self.cmdline:
            resplines = resplines[1:]
        if resplines[-1].startswith(self.prompt.strip()):
            resplines = resplines[:-1]

        return resplines

    def resp(self):
        """Return raw response as list of lines.
        Excludes original command and prompt after command.
        """
        resplines = []
        for line in self.raw.splitlines():
            resplines.append(line.strip())
        if resplines[0] == self.cmdline:
            resplines = resplines[1:]
        if resplines[-1].startswith(self.prompt.strip()):
            resplines = resplines[:-1]

        return resplines
