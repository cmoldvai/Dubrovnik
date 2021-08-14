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

        #CM TODO: check if it works
        self.inWaitingBytes = None

        # additional attributes
        self.vrfyout = sys.stdout       # default verify-out
        self.vrfyprogress = False       # default verify report progress

    def serialAvailable(self):
        try:
            numBytes = self.handle.in_waiting
            self.inWaitingBytes = numBytes
            print(f'Number of in bytes: {numBytes}')
            # time.sleep(1)
            return numBytes
        except Exception as e:
            resp = f'error from boardcom: {e}'
            print(resp)
            comm.disconnect(comPort, echo=1)

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

    def connect(self, comport, echo=0):
        try:
            self.handle = serial.Serial(comport, self.baudrate, timeout=600)
            comm.handle = self.handle
            print(comm.handle)
            print(self.handle)
        except serial.SerialException:
            print("Error: cannot open", comport)
            raise IOError("cannot open " + comport)

        print(f'Connected to {comport}...')
        return self.handle
        # return comport

    def disconnect(self, comport, echo=0):
        if comport:
            self.handle.close()
            # print(self.handle)
        if echo:
            print(f'\nDisconnected from {comport}...')

    def find_and_connect(self, desiredPort='auto', echo=0):
        '''
        Finds all USB ports that have a Dubronik board connected to and lists them
        We can specify the desired port
        Parameters:
            desiredPort : integer value or the port we want to connect to. This can be useful
                          when we want to connect to a specific dubrovnik board. If for some reason
                          that board is not available (turned off, or not workink) we will get 
                          an error message
                          'auto' will select the first element of portList
            echo : if '1' it will print the list of available ports (portList)
        Returns the port name (COMn) it is connected to
        Example:
        comm is an instance of BoardComm
        connectedPort = comm.find_and_connect()
        connectedPort = comm.find_and_connect(echo=1)
        connectedPort = comm.find_and_connect(desiredPort=5, echo=1) 
        connectedPort = comm.find_and_connect(desiredPort=5) 
        '''
        portList = self.findPorts()
        if echo == 1:
            print(portList)
        if desiredPort == 'auto':
            connectedPort = portList[0]
        else:
            connectedPort = f'COM{desiredPort}'
        self.connect(connectedPort)
        return connectedPort

    def autoConnect(self, defaultPort):
        '''Automatically connect to defaultPort if specified'''
        portList = self.findPorts()
        if portList:
            port = portList[0]
            self.connect(port)

    def send(self, cm):
        """Send a command line 'cm' to serial port and await prescribed prompt.
        """
        # self.cmdline = cm   # original location. Moved after adding '\r'
        # print("SEND", cm)   # uncomment for low level command debugging
        if cm[-1] != '\r':
            cm += '\r'
        self.cmdline = cm

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
                # print("Could not find prompt; so far read:")
                # print(s)
                return 1

            c = b.decode('utf-8')
            self.raw += c
            # print("bm raw", self.raw)
            if self.raw.endswith(self.prompt):
                # ok = True
                self.cooked = self.raw.lower()
                # print ("cooked:", self.cooked)
                self.handle.flush()  #CM TODO: check if needed
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

    # Original function
    # def response(self):
    #     """Get respond from last command.
    #     """
    #     return self.cooked

    def response(self, longResponse=True):
        """Get respond from last command.
        """
        if not 'longResponse':
            return self.cooked
        else:
            pref_len = len(self.cmdline)
            suff_len = len(self.prompt)
            # We do not want any trailing whitespace.
            return self.cooked.strip()[pref_len:-(suff_len)].strip()

    def responselines(self, longResponse=True):
        """Return raw response as list of lines.
        Excludes original command and prompt after command.
        """
        resplines = []
        # split response into separate lines
        for line in self.raw.splitlines():
            resplines.append(line.strip())

        if not longResponse:
            # if first element matches cmdline
            if resplines[0] == self.cmdline:
                resplines = resplines[1:]  # remove it
            # if last element is prompt
            if resplines[-1].startswith(self.prompt.strip()):
                resplines = resplines[:-1]  # remove it

        return resplines

    def resp(self):
        """Return raw response as list of lines.
        Excludes original command and prompt after command.
        """
        resplines = []
        for line in self.raw.splitlines():
            resplines.append(line.strip())
        if resplines[0] == self.cmdline[:-1]:
            resplines = resplines[1:]
        if resplines[-1].startswith(self.prompt.strip()):
            resplines = resplines[:-1]

        return resplines


if __name__ == '__main__':
    
    import threading

    comm = BoardComm()
    comPort = comm.find_and_connect(echo=1)

    cmdList = ['b 0 2;wait 0', '05', 'dvar wait_time', '35']
    # print(dir(serial))
    
    # T1 = threading.Thread(target=comm.serialAvailable)
    # T1.start()
    # T1._stop

    for cmd in cmdList:
        print(cmd)
        comm.send(cmd)
        time.sleep(.5)

        t1 = time.perf_counter()

        # comm.serialAvailable()
        if comm.serialAvailable() != 0:
        # if comm.inWaitingBytes != 0:
            print(comm.response())


        t2 = time.perf_counter()
        print(f'ETE: {round(t2-t1,6)} second(s)')

    comm.serialAvailable()
    print(f'Number of inBuffer Bytes: {comm.inWaitingBytes}')
    print(comm.response())
