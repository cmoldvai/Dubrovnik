import time
from dubLibs import boardcom


class DpmEK():
    def __init__(self, comm):
        self.comm = comm
        # Reset values (default)
        self.brng = 2  # don't use 3, to avoid having duplicate '60V' in GUI
        self.pg = 3
        self.badc = 3
        self.sadc = 3
        self.mode = 7
        # Board Dependent
        self.rshunt = 0.1

        self.vbus_range_tbl = [16, 32, 60, 60]
        # Table converting config register BRNG field value to bus voltage range.
        # The field value is an index to the table

        self.vshunt_range_tbl = [0.04, 0.08, 0.16, 0.32]
        # Table converting config register PG field value to shunt voltage range.
        # The field value is an index to the table.

        self.conv_time_us_tbl = [72, 132, 258, 508, 72, 132, 258, 508,
                                 508, 1010, 2010, 4010, 8010, 16010, 32010, 64010]
        # Table converting config register BADC and SADC field values to sample conversion times.
        # The field value is an index to the table. The table values are expressed in microseconds

    def set_config(self):
        ''' This function sets the DPM configuration register. It generates the config register value from
        the values of its fields: BRNG, PG, BADC, SADC and MODE. Then it writes the generated value
        into the config register. The config register field values are the arguments to the function.'''
        w = (self.brng << 13) | (self.pg << 11) | (
            self.badc << 7) | (self.sadc << 3) | self.mode
        # print(f'{w:x}')
        self.comm.send(f'wr 0 {w:x}')

    def set_calibration(self):
        ''' This function sets the DPM calibration register. It calculates the calibration register
        value based on equations described in the datasheet. Note that these equations can be be simplified
        as shown below. At the end the calibration value depends only on the shunt voltage range or Vshunt
        Full Scale (VshuntFS) which can be obtained from the PG field of the config register. This field's
        value is the argument to this function.
        Below we develop the datasheet equations:

        CalRegval =
        0.04096 / (CurrentLSB * Rshunt) =
        (0.04096 * ADCres) / (CurrentFS * Rshunt) =
        (0.04096 * ADCres * Rshunt) / (VshuntFS * Rshunt) =
        (0.04096 * ADCres) / VshuntFS =
        (0.04096 * 32768) / VshuntFS =
        1342.177 / VshuntFs
        '''
        vshuntfs = self.vshunt_range_tbl[self.pg]
        w = int(1342.177 / vshuntfs)
        self.comm.send(f'wr 5 {w:x}')

    def set_vshunt_threshold(self, minv, maxv):
        ''' This function sets the shunt voltage threshold register. It takes 2 floating point
        arguments which are the desired min and max shunt voltage threshold values. From these
        values it generates the bit value of the shunt voltage threshold register and writes it
        to the register.'''
        minv_bitfield_value = int(minv / 0.00256)
        if minv_bitfield_value > 127 or minv_bitfield_value < -128:
            return
        if minv_bitfield_value < 0:
            minv_bitfield_value = (128 - abs(minv_bitfield_value)) | 0x80
        maxv_bitfield_value = int(maxv / 0.00256)
        if maxv_bitfield_value > 127 or maxv_bitfield_value < -128:
            return
        if maxv_bitfield_value < 0:
            maxv_bitfield_value = (128 - abs(maxv_bitfield_value)) | 0x80
        w = minv_bitfield_value | (maxv_bitfield_value << 8)
        self.comm.send(f'wr 6 {w:x}')

    def set_vbus_threshold(self, minv, maxv):
        ''' This function sets the bus voltage threshold register. It takes 2 floating point
        arguments which are the desired min and max bus voltage threshold values. From these
        values it generates the bit value of the bus voltage threshold register and writse it
        to the register.'''
        minv_bitfield_value = int(minv / 0.256)
        if minv_bitfield_value > 255 or minv_bitfield_value < 0:
            return
        maxv_bitfield_value = int(maxv / 0.256)
        if maxv_bitfield_value > 255 or minv_bitfield_value < 0:
            return
        w = minv_bitfield_value | (maxv_bitfield_value << 8)
        self.comm.send(f'wr 7 {w:x}')

    def read_bus_voltage(self):
        ''' This function reads the bus voltage register and calculates the bus voltage
        It returns the bus voltage in volts (floating point value). It receives one argument,
        the value of the BRNG fieled of the config register - it expresses the bus voltage
        range which is required for interpreting the bus voltage register value.'''
        self.comm.send('rr 2')
        resp = self.comm.response(removeCmd=True, returnAsList=False)
        w = int(resp, 16)
        if self.brng == 0:  # 16V (12 bits)
            w = (w >> 3) & 0x0fff
        elif self.brng == 1:  # 32V (13 bits)
            w = (w >> 3) & 0x1fff
        else:  # 60V (14 bits)
            w = (w >> 2) & 0x3fff
        voltage = float(w) * 0.004  # lsb = 4mV
        return voltage

    def read_shunt_voltage(self):
        ''' This function reads the shunt voltage register and calculates the shunt voltage
        It returns the shunt voltage in volts (floating point value). It receives one argument,
        the value of the PG fieled of the config register - it expresses the shunt voltage
        range which is required for interpreting the shunt voltage register value.'''
        self.comm.send('rr 1')
        resp = self.comm.response(removeCmd=True, returnAsList=False)
        w = int(resp, 16)
        if self.pg == 0:
            sign_pos = 12
            tc = 4096
        elif self.pg == 1:
            sign_pos = 13
            tc = 8192
        elif self.pg == 2:
            sign_pos = 14
            tc = 16384
        else:
            sign_pos = 15
            tc = 32768
        sign = (w >> sign_pos) & 0x0001
        tc = 1 << sign_pos
        mask = tc - 1
        w = (w & mask) - (sign * tc)
        voltage = float(w) * 0.00001  # lsb = 10uV
        return voltage

    def read_current(self):
        ''' This function reads the current register and calculates the current.
        It returns the current in amps (floating point value). It receives two
        arguments which ar enecessary for the current calculation:
        - The value of the PG field of the config register representing the shunt voltage
        range (a.k.a. Vshunt full scale or VshuntFS)
        - The shunt resistor's resistance in Ohms.'''
        vshuntfs = self.vshunt_range_tbl[self.pg]
        self.comm.send('rr 4')
        resp = self.comm.response(
            removeCmd=True, returnAsList=False)
        w = int(resp, 16)
        sign = (w >> 15) & 0x0001
        w = (w & 0x7fff) - (sign * 32768)
        currentfs = vshuntfs / self.rshunt
        currentlsb = currentfs / 32768
        cur = float(w) * currentlsb
        return cur

    def read_power(self):
        ''' This function reads the power register and calculates the power.
        It returns the power in watts in amps (floating point value). It receives two
        arguments which ar enecessary for the power calculation:
        - The value of the PG field of the config register representing the shunt voltage
        range (a.k.a. Vshunt full scale or VshuntFS)
        - The value of the BRNG field of the config register representing the bus voltage
        range (a.k.a. Vbus full scale or VbusFS)
        - The shunt resistor's resistance in Ohms.'''
        vshuntfs = self.vshunt_range_tbl[self.pg]
        self.comm.send('rr 3')
        resp = self.comm.response(removeCmd=True, returnAsList=False)
        w = int(resp, 16)
        currentfs = vshuntfs / self.rshunt
        currentlsb = currentfs / 32768
        powerlsb = currentlsb * 0.004  # Vbus lsb = 4mV
        # power = w * powerlsb * 5000
        power = w * powerlsb * 5000000  # TEST to get large numbers in GUI
        if self.brng >= 2:  # implying VbusFS=60V
            power = power * 2
        return power

    def readRegisters(self):
        vals = []
        for n in range(10):
            self.comm.send(f'rr {n:x}')
            resp = self.comm.response(
                removeCmd=True, returnAsList=False)
            vals.append(resp)
        return vals

    def get_threshold_int_status(self):
        ''' This function reads the interrupt status register and extracts the 4
        interrupt status bits. It returns an integer with these 4 interrupt bits:
        Bit 0 (BMNW): 1 indicates bus voltage below minimum
        Bit 1 (BMXW): 1 indicates bus voltage above maximum
        Bit 2 (SMNW): 1 indicates shunt voltage below minimum
        Bit 3 (SMXW): 1 indicates shunt voltage above maximum'''
        self.comm.send('rr 8')
        resp = self.comm.response(removeCmd=True, returnAsList=False)
        w = int(resp, 16) & 0xf
        return w


if __name__ == '__main__':

    cm = boardcom.BoardComm()   # create an instance of class BoardComm
    connectedPort = cm.find_and_connect(echo=1)
    dpm = DpmEK(cm)

    dpm.brng = 0x0  # 16V
    dpm.pg = 0x3  # 320mV
    dpm.badc = 0x9  # 1.01ms
    dpm.sadc = 0xf  # 64.01ms
    dpm.mode = 0x7  # shunt & bus continuous
    dpm.rshunt = 1.0

    dpm.set_config()
    dpm.set_calibration()
    dpm.set_vshunt_threshold(0.02, 0.06)
    dpm.set_vbus_threshold(2.0, 4.0)

    print("### continouously read measurements for one minute ###")

    t_elapsed = 0
    t_start = time.time()

    while t_elapsed < 60.0:
        print(f'vbus = {dpm.read_bus_voltage():.3f}V ', end='')
        print(f'vshunt = {dpm.read_shunt_voltage():.3f}V ', end='')
        print(f'current = {dpm.read_current():.3f}A ', end='')
        print(f'power = {dpm.read_power():.2f}mW ', end='')

        # print(
        #     f"vbus = {dpm.read_bus_voltage():.3f}V ", end="")
        # print(
        #     f"vshunt = {dpm.read_shunt_voltage():.3f}V ", end="")
        # print(
        #     f"current = {dpm.read_current():.3f}A ", end="")
        # print(
        #     f"power = {dpm.read_power():.2f}mW ", end="")
        ints = dpm.get_threshold_int_status()
        print(f"interrupt status = {ints:04b}")
        if ints != 0:
            cm.send("wr 8 f")
        time.sleep(2.0)
        t_elapsed = time.time() - t_start
