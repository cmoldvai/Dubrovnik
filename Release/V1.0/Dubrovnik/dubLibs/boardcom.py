"""
boardcom: Board Communications
Implemented as a class providing access to:
send(command)
resp = response()
"""

from dubGui.dubGuiDev.serialTerminalShell import PROMPT
import sys
import time
import serial
from serial.tools.list_ports import comports
from tkinter.messagebox import askretrycancel

PROMPT = b">>> "

# Keep reading from serial line until full prompt is seen


class BoardComm:
    """wrapper for communications interface
    """

    # CM TODO: changed prompt from ">>>" to ">>> ". This reduced the in_waiting bytes form 1 to 0.
    def __init__(self, prompt=">>> ", icpause=None, baudrate=115200):
        """Initialize with:
        port - serial communication port, e.g., "COM3"
        prompt - match prompt, e.g., "Fusethat >>>"; default is ">>>"
        icpause - inter-character pause in seconds
        """
        self.port = None
        self.prompt = prompt.encode('utf-8')  # prompt must be a byte: b'>>> '
        self.icpause = icpause
        self.baudrate = baudrate
        self.handle = None
        self.cmdline = ""       # utf-8 version of the command line
        self.raw = ""           # unprocessed response (utf-8, 8-bit ascii)
        self.cooked = ""        # processed response (.decode(utf-8).lower())

        # CM TODO: check if it works
        # CM TODO: was None. Failed with: "None type has no attribute 'in_waiting'
        self.inWaitingBytes = 0  # number of bytes waiting in the in_buffer

        # additional attributes
        self.vrfyout = sys.stdout       # default verify-out
        self.vrfyprogress = False       # default verify report progress

    def connect(self, comport, echo=1):
        try:
            self.handle = serial.Serial(comport, self.baudrate, timeout=600)
            # print(self.handle)
        except serial.SerialException:
            print("Error: cannot open", comport)
            raise IOError("cannot open " + comport)

        if echo:
            print(f'Connected to {comport}...')
        return self.handle
        # return comport

    def disconnect(self, comport, echo=1):
        if comport:
            self.handle.close()
            # print(self.handle)
        if echo:
            print(f'\nDisconnected from {comport}...')

    def serialAvailable(self):
        prev_numBytes = 0
        curr_numBytes = self.handle.in_waiting
        time.sleep(.05)

        # waiting until number of in_waiting bytes stabilize
        for i in range(3):
            if curr_numBytes >= prev_numBytes:
                prev_numBytes = curr_numBytes
                curr_numBytes = self.handle.in_waiting
            else:
                print("ERROR! Number of bytes in the buffer decreased")
                return(-1)
            time.sleep(.05)
            print(f'{i}: Running total of waiting bytes: {curr_numBytes}')

        self.inWaitingBytes = curr_numBytes
        print(f'final in_buffer waiting bytes: {curr_numBytes}')
        return curr_numBytes  # 0 or number of waiting bytes in the in_buffer

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

    # ********************************************************
    # New send/recv functions for use in the terminal window
    # ********************************************************

    def send(self, cmdstr):
        self.handle.reset_input_buffer()  # in case we have back to back send commands

        if cmdstr[-1] != '\r':  # TestBench expects a newline
            cmdstr += '\r'      # append if not already there

        self.cmdline = cmdstr
        byteseq = cmdstr.encode('utf-8')  # convert to ASCII/UTF-8
        numBytesSent = self.handle.write(byteseq)  # send to port
        # # must allow some time for the response from TestBench to arrive
        # # min 0.006 sec for 0x1000 bytes, 0.025 sec for 0x4000 bytes.
        # time.sleep(0.02)

        # Read back content of in-buffer (empty it), then save response in raw and cooked
        self.raw = ""
        self.cooked = ""
        self.raw = self.handle.read_until(expected=PROMPT).decode('utf-8')
        self.cooked = self.raw.lower()
        self.response()

        return numBytesSent

    def response(self, removeCmd=False, removePrompt=True, returnAsList=False, readBuffer=False):
        if readBuffer:
            self.raw = ""
            self.cooked = ""
            self.raw = self.handle.read_until(expected=PROMPT).decode('utf-8')
            self.cooked = self.raw.lower()

        if removeCmd:
            start_idx = len(self.cmdline)
        else:
            start_idx = 0

        if removePrompt:
            # CM Replaced self.cooked with self.raw to preserve
            # capital letters in printouts, e.g. PMON, Voltage
            end_idx = len(self.raw) - len(PROMPT)
        else:
            end_idx = len(self.raw)

        # remove the last '\r'. Some responses will have an extra SPACE. Can remove, though
        resp = self.raw[start_idx:end_idx-1]

        if returnAsList:
            return resp.splitlines()
        else:
            return resp

    # def send(self, cm):
    #     """Send a command line 'cm' to serial port and await prescribed prompt.
    #     """
    #     # self.cmdline = cm   # original location. Moved after adding '\r'
    #     # print("SEND", cm)   # uncomment for low level command debugging
    #     if cm[-1] != '\r':
    #         cm += '\r'
    #     self.cmdline = cm

    #     if not self.icpause:
    #         byteseq = cm.encode('utf-8')  # convert to ASCII/UTF-8
    #         self.handle.write(byteseq)  # send to port
    #     else:
    #         for bb in cm:
    #             bytes = bb.encode('utf-8')
    #             self.handle.write(bytes)
    #             time.sleep(self.icpause)
    #     self.raw = ""
    #     self.cooked = ""
    #     while True:
    #         b = self.handle.read(1)
    #         if len(b) == 0:
    #             # We can only get here due to timeout
    #             # print("Could not find prompt; so far read:")
    #             # print(s)
    #             return 1

    #         c = b.decode('utf-8')
    #         self.raw += c
    #         # print("bm raw", self.raw)
    #         if self.raw.endswith(self.prompt):
    #             # ok = True
    #             self.cooked = self.raw.lower()
    #             # print ("cooked:", self.cooked)
    #             return 0

    # def set_vrfy_attrs(self, vrfyout=None, vrfyprogress=None):
    #     """Set 'sendvrfy' attributes
    #     vrfyout : file stream for command output
    #     vrfyprogress : report progress when done
    #     """
    #     # This probably would be keyword recognition
    #     if vrfyout:
    #         self.vrfyout = vrfyout
    #     if vrfyprogress:
    #         self.vrfyprogress = vrfyprogress

    # def sendvrfy(self, cm, annotation=None, showout=False, reflines=None):

    # def sendvrfy(self, cm, annotation=None, reflines=None):
    #     """Send a command 'cm' and optionally verify result via 'assert'.
    #     This method produces text
    #     If annotation not provided, 'assert' will use 'cm'.
    #     If 'progress' is True, inform when done.
    #     """
    #     vout = self.vrfyout     # verify-out stream
    #     self.send(cm)
    #     resp = self.response()
    #     if annotation is None:
    #         annotation = cm

    #     # verify successful completion of command
    #     assert resp.endswith(self.prompt), annotation
    #     if self.vrfyprogress:
    #         print(" .", annotation, "done", file=vout)
    #     resplines = self.responselines()
    #     if reflines:
    #         matched = True
    #         for ref, got in zip(reflines, resplines):
    #             assert ref == got, annotation
    #             if ref != got:
    #                 matched = False
    #                 break
    #         if not matched:
    #             matched = False

    #         return matched
    #     else:
    #         return True

    # Original function
    # def response(self):
    #     """Get respond from last command.
    #     """
    #     return self.cooked

    # def response(self, removeCmd=False, removePrompt=False, returnAsList=False):
    #     """Get respond from last command.
    #     """
    #     if removeCmd:
    #         start_idx = len(self.cmdline)
    #     else:
    #         start_idx = 0

    #     if removePrompt:
    #         end_idx = len(self.cooked) - len(self.prompt)
    #     else:
    #         end_idx = len(self.cooked)

    #     resp = self.cooked[start_idx:end_idx]
    #     self.inWaitingBytes = 0

    #     if returnAsList:
    #         return resp.splitlines()
    #     else:
    #         return resp

    # # CM TODO: delete responselines and resp. Update the rest of the code to work with response(args)
    # def responselines(self, longResponse=True):
    #     """Return raw response as list of lines.
    #     Excludes original command and prompt after command.
    #     """
    #     resplines = []
    #     # split response into separate lines
    #     for line in self.raw.splitlines():
    #         resplines.append(line.strip())

    #     if not longResponse:
    #         # if first element matches cmdline
    #         if resplines[0] == self.cmdline:
    #             resplines = resplines[1:]  # remove it
    #         # if last element is prompt
    #         if resplines[-1].startswith(self.prompt.strip()):
    #             resplines = resplines[:-1]  # remove it

    #     return resplines

    # def resp(self):
    #     """Return raw response as list of lines.
    #     Excludes original command and prompt after command.
    #     """
    #     resplines = []
    #     for line in self.raw.splitlines():
    #         resplines.append(line.strip())
    #     if resplines[0] == self.cmdline[:-1]:
    #         resplines = resplines[1:]
    #     if resplines[-1].startswith(self.prompt.strip()):
    #         resplines = resplines[:-1]
    #     return resplines


if __name__ == '__main__':
    # import threading
    # comm = BoardComm()
    # comPort = comm.find_and_connect(echo=0)
    # comm.disconnect(comPort, echo=0)
    comm = BoardComm()
    comPort = comm.find_and_connect(echo=1)

    # cmdList = ['5', '0b 00 20;wait 00', 'dvar wait_time']

    # for cmd in cmdList:
    #     # comm.send(cmd)
    #     resp = comm.term_send(cmd, getResponse=True, removeCmd=False, removePrompt=False, returnAsList=False)
    #     print(resp)

    comm.send('b 0 400; wait 0')
    print(comm.response())

    comm.send('b 0 100')
    print(comm.response())

    comm.send('dvar wait_time')
    print(comm.response())

    # while not comm.serialAvailable():
    #     pass
    # resp = comm.response()
    # print(resp)

    comm.disconnect(comPort, echo=1)

    # cmdList = ['b 0 2;wait 0', '05', 'dvar wait_time', '35']
    # # T1 = threading.Thread(target=comm.serialAvailable)
    # # T1.start()
    # for cmd in cmdList:
    #     print(cmd)
    #     comm.send(cmd)
    #     time.sleep(1)

    #     t1 = time.perf_counter()
    #     if comm.serialAvailable(comPort) != 0:
    #         print(comm.response())
    #     t2 = time.perf_counter()
    #     print(f'ETE: {round(t2-t1,6)} second(s)')

    # # comm.serialAvailable()
    # # print(f'Number of inBuffer Bytes: {comm.inWaitingBytes}')
    # print(comm.response())
