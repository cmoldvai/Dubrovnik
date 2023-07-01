"""
boardcom: Board Communications
Implemented as a class providing access to:
send(command)
resp = response() and other useful function required to communicate
with the Dubrovnik board.
"""

import sys
import time
import serial
from serial.tools.list_ports import comports
from tkinter.messagebox import askretrycancel, showerror

# PROMPT = b">>> "  # ? Is anyone using this?


class BoardComm:
    """wrapper for communications interface
    """

    # changed prompt from ">>>" to ">>> ". This reduced the in_waiting bytes form 1 to 0.
    def __init__(self, prompt=">>> ", icpause=None, baudrate=115200):
        """Initialize with:
        port - serial communication port, e.g., "COM3"
        prompt - match prompt, e.g., "Fusethat >>>"; default is ">>>"
        icpause - inter-character pause in seconds
        """
        self.port = None
        self.prompt = bytes(prompt, 'utf-8')  # prompt MUST be a byte
        self.icpause = icpause
        self.baudrate = baudrate
        self.handle = None
        self.cmdline = ""        # utf-8 version of the command line
        self.raw = ""            # unprocessed response (utf-8, 8-bit ascii)
        # ? processed response (.decode(utf-8).lower()). Is anyone using this?
        self.cooked = ""
        # holds text that need to printed (GUI or elsewhere)
        self.textToDisplay = ""
        self.inWaitingBytes = 0  # number of bytes waiting in the in_buffer
        self.vrfyout = sys.stdout       # default verify-out
        self.vrfyprogress = False       # default verify report progress

    def connect(self, comport, echo=1):
        try:
            self.handle = serial.Serial(
                comport, self.baudrate, timeout=2)  # ! was: timeout=600
            # print(self.handle)
        except serial.SerialException:
            print("Error: cannot open", comport)
            # raise IOError("cannot open " + comport)
            askretrycancel('Comport Error', f'Cannot open port {comport}\n \
                           Make sure it is not used by another program')
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
        """### Reads Windows USB Serial Port Properties
        Returns a list of COM ports that have 'FTDI' as manufacturer. Some COM ports
        may be 'FTDI', but not Dubrovnik boards. These ports are not valid for our app
        """
        portList = []
        ports = serial.tools.list_ports.comports()
        for i in range(len(ports)):
            if ports[i].manufacturer == 'FTDI':  # find ports made by 'FTDI'
                portList.append(ports[i].device)
        return portList

    def findPorts(self):
        """findPorts() keeps calling getPortList until a port is found or the operation is aborted.\n
        In case a communication port is not avaiable (e.g. USB cable not connected, Dubrovnik board
        not turned on, or the RESET button was not pressed) a dialog box keeps popping-up until the
        situation is remedied ("Retry") or the operation is cancelled in which case the program quits.\n
        Returns the sorted list of found ports (portList) or quits the program if no valid port was found.
        """
        portList = self.getPortList()
        if portList == []:
            showerror('Dubronik Dashboard Error (dubrovnik.py findPorts)',
                      'Serial COM Port Not Found!\n\n1. Connect USB cable\n2. Turn on the board\n3. Press RESET button\n4. Restart the application')
            sys.exit()
        portList.sort()  # in-place sorting of the list
        return portList  # return sorted port list

        # while portList == []:
        #     if askretrycancel('Dubrovnik Dashboard (dubrovnik.py) Error',
        #                       'COM Port Not Found!\nConnect USB cable.\nTurn on the board.\nPress RESET button.\nRetry?'):
        #         portList = self.getPortList()
        #     else:
        #         sys.exit
        #         break
        # portList.sort()  # in-place sorting of the list
        # return portList  # return sorted port list

    def find_and_connect(self, desiredPort='auto', echo=0):
        """### Finds all USB serial ports that have a potential Dubronik board connected to it
        It is possible to specify a desired COM port to connect to.
        Parameters:
        * desiredPort : integer value or the port we want to connect to.\n
        This can be useful when we want to connect to a specific dubrovnik board. If for some reason
        that board is not available (turned off, or not workink) we will get an error message.\n
          'auto' will select the first element of portList
        * echo : if '1', it will print the list of available ports (portList)
        Returns the port name (COMn) it connected to.
        Example:
        comm is an instance of BoardComm
        connectedPort = comm.find_and_connect()
        connectedPort = comm.find_and_connect(echo=1)
        connectedPort = comm.find_and_connect(desiredPort=5, echo=1)
        connectedPort = comm.find_and_connect(desiredPort=5)
        """
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

    def connectToMCU(self):
        """### Connects to the MCU on Dubrovnik board
        Prerequisite: must be connected to the USB-to-UART chip on Dubrovnik via a COM port\n
        A 'ver' command is sent out. If MCU does not respond, a pop-up dialog will prompt the
        user to press RESET button which forces the MCU to boot and print a RESET message that
        contains a row of stars: '*****'. The function is checking for this to detect if MCU responded.
        """
        self.send('ver')  # sends out a message to the board (not the flash, yet)
        resp = self.response()
        self.textToDisplay = resp  # save response for printing

        if "ver" in resp:  # the MCU responded to ver command. We have comms with MCU
            # print(resp)
            pass
        elif '*****' in resp:  # this is a response when the RESET button was pressed
            print('Clearing RESET message from the input buffer')
            self.handle.reset_input_buffer()  # in that case clear the input buffer
        else:    # wrong response
            print("Wrong response. No response already checked for in self.reponse()")

        # increase serial timeout for long Erase times (minutes)
        self.handle.timeout = 200
        print(self.handle.get_settings())  # TODO sometimes long timeout not set
        return resp

    def isFlashPresent(self):
        """### Checking if flash is present on the board and responding
        By this time we should have communication with the board.\n
        Now we check if it is possible to talk to the flash device.\n
        Returns 0: if flash partNumber is 'unknown' (meaning: flash not installed
        or doesn't respond. 1: if partNumber is different than 'unknown'
        """
        cfg = []
        self.send('config')
        cfg = self.response(
            removeCmd=True, removePrompt=True, returnAsList=True)
        try:
            partNum = cfg[0].split('=')[1].strip().lower()
            # print(partNum)
        except IndexError:
            return 0  # TODO under some conditions even after reset cfg invalid

        if partNum == 'unknown':
            return 0  # flash doesn't respond
        else:
            return 1  # a part is present on the board and responds.

    # ********************************************************
    # New send/recv functions for use in the terminal window
    # ********************************************************

    def send(self, cmdstr):
        """### Sends a command string to TestBench
        After the command was sent it reads the response from the input buffer
        until the expected prompt is received.\n
        It handles corner cases when the board is not turned on, or the reset
        button was not pressed on Dubrovnik board. A dialog allows to Retry or Cancel
        Paremeters:
        * comm   : handle of the communication port
        * cmdstr : the command string to be sent to the board\n
        Returns the number of bytes sent (int)
        """
        self.handle.reset_input_buffer()  # in case we have garbage in in-box (shouldn't happen)

        if cmdstr[-1] != '\r':  # TestBench expects a newline
            cmdstr += '\r'      # append if not already there

        self.cmdline = cmdstr
        byteseq = cmdstr.encode('utf-8')  # convert to ASCII/UTF-8
        numBytesSent = self.handle.write(byteseq)  # send to port
        # time.sleep(0.03)
        # sleep() is used if the last command of send() function is not a response().
        # Allows some time for the response from TestBench to arrive
        # min 0.006 sec for 0x1000 bytes, 0.025 sec for 0x4000 bytes.

        # Read back content of in-buffer (empty it), then save response in "raw" and "cooked"
        self.raw = ""
        self.cooked = ""
        self.raw = self.handle.read_until(expected=self.prompt).decode('utf-8')

        while self.raw == "":
            # if no response from the board (raw=="") after timeout, pop up a RETRY/CANCEL dialog
            if not askretrycancel('Communication Error: Serial Port Timeout',
                                  'Is the board turned ON?\nPress the RESET button'):
                sys.exit()
            self.raw = self.handle.read_until(
                expected=self.prompt).decode('utf-8')

        self.cooked = self.raw.lower()
        # RECOMMENDED to get a response. If not, after a back-to-back "send()" command we must have
        # a blind wait (established experimentally) allowing all data to arrive from TestBench, before
        # the next send command is sent, otherwise it will mess up the input buffer.
        # The wait time depends on the lenght of the response, which we don't know ahead of time.
        self.response()

        return numBytesSent

    def response(self, removeCmd=False, removePrompt=True, returnAsList=False, readInBuffer=False):
        """### Get a response from TestBench
        If no response is received, a pop-up dialog will prompt the user to turn on or reset the board
        (which may remedy the situation). If "Cancel" is pressed, the program quits.\n
        Parameters:\n
        * removeCmd    : if True, removes the echo'd command string from the beginning of the response string
        * removePrompt : if True, removes the prompt from the end of the response string
        * returnAsList : if True, returns the response string as 1-3 element list: ['cmd string', 'response string', 'prompt']
        * readInBuffer : if True, reads the input buffer, (get data from serial port). Used when we want asynchrously to read
        the input buffer, without sending the send(cmd) first e.g. when trying to capture the message when RESET button was pressed.
        """
        if readInBuffer:
            self.raw = ""       # raw data from the serial port input buffer
            self.cooked = ""    # data converted to lower case
            self.raw = self.handle.read_until(
                expected=self.prompt).decode('utf-8')
            self.cooked = self.raw.lower()

        if removeCmd:
            start_idx = len(self.cmdline)
        else:
            start_idx = 0

        if removePrompt:
            # Replaced self.cooked with self.raw to preserve
            # capital letters in printouts, e.g. PMON, Voltage
            end_idx = len(self.raw) - len(self.prompt)
        else:
            end_idx = len(self.raw)

        # remove the last '\r'. SOME responses will have an extra SPACE.
        resp = self.raw[start_idx:end_idx-1]

        if returnAsList:
            return resp.splitlines()
        else:
            return resp

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
