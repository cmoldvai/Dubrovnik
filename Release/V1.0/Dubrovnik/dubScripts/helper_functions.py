# ############################################################################
# ### ------------- helper functions --------------
# ############################################################################

# -----------------------------------------------------------------------------
# *** update_byte
# -----------------------------------------------------------------------------
def update_byte(old_byte, mask, data):
    new_byte = (old_byte & ~mask) | (data & mask)
    return new_byte


# -----------------------------------------------------------------------------
# *** tohex
# -----------------------------------------------------------------------------
def tohex(num):
    """
   This function will take a number and format it
   into a hex string for use on the dubrovnik

   Parameters
   ----------
   The function requires 1 input arguments,
    num :         unsigned integer value to change to string (1 byte)

   The function will return a the hex string
   representaion of the least significant byte

   Examples
   --------
   bs = tohex(0x22)
   out: '22'
   print(tohex(0x3)
   out: '03'
   """

    if type(num) is int:
        bs = format(num, "02x")
    elif type(num) is str:
        if 'x' in num:
            bs = num.split('x')[-1]
        else:
            bs = num
    else:
        try:
            bs = format(int(num), "02x")
        except Exception:
            bs = format(int(num, 16), "02x")

    return bs


# -----------------------------------------------------------------------------
# *** hiz
# -----------------------------------------------------------------------------
def hiz(comm, onoff):
    """
   Thus function will turn on the HiZ mode on/off the dubrovnik board

   Parameters
   ----------
   The function requires 1 input arguments,
    comm :         The handle to the comm port to communicate with the
                     Dubrovnik board
   The function has no return

   Examples
   --------

   """

    if onoff.lower() == 'on':
        comm.send("c4 d0")
    elif onoff.lower() == 'off':
        comm.send("00")
    else:
        print("Valid values for onoff are: ['on', 'off'].")

    return None


# -----------------------------------------------------------------------------
# {{{ dub_getconfig
# -----------------------------------------------------------------------------
def dub_getconfig(comm):
    """
   This function will fetch the configuration parameters
   from the dubrovnik board

   Parameters
   ----------
   The function requires 2 input arguments,
    comm :          The handle to the comm port to communicate with the
                      Dubrovnik board

   The function returns a dictionary of strings of the configuration parameters

   Examples
   --------
   params = dub_getconfig(comm)

   part = params['part']
   voltage = params['voltage']
   frequency = params['frequency']
   dummycount = params['dummycount']
   hostds = params['hostds']

   for key, value in params.items():
       print(key+' '+value)

   """

    paramlist = commtxrx(comm, "config", joinlines=False).splitlines()
    part = paramlist[0].split(" ")[-1]
    voltage = paramlist[1].split(" ")[-1]
    frequency = paramlist[2].split(" ")[-1]
    dummycount = paramlist[3].split(" ")[-1]
    hostds = paramlist[4].split(" ")[-1]

    return {
        "part": part,
        "voltage": voltage,
        "frequency": frequency,
        "dummycount": dummycount,
        "hostds": hostds,
    }


# -----------------------------------------------------------------------------
# *** dub_setconfig
# -----------------------------------------------------------------------------
def dub_setconfig(
    comm, part=None, vcc=None, freq=None, dummys=None, hostds=None
):
    """
   This function will configures the part, vcc, frquency, dummycount,
    and hostds for the boardmon

   Parameters
   ----------
   The function requires 6 input arguments,
    part :          part id to send to the boardmon
    vcc :           sets the vcc
    freq :          sets the frequency
    dummys :        sets the dummycount
    hostds : sets the hostds
   The function has no return

   Examples
   --------
   """

    if part is not None:
        comm.send("setpart " + str(part))
    if vcc is not None:
        comm.send("volt " + str(vcc))
    if freq is not None:
        comm.send("freq " + str(freq))
    if dummys is not None:
        comm.send("dummy " + str(dummys))
    if hostds is not None:
        comm.send("hostds " + str(hostds))

    return None


# -----------------------------------------------------------------------------
# END OF FILE
# -----------------------------------------------------------------------------
