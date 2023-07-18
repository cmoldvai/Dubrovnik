import time
from dubLibs import boardcom
from dubLibs import dubrovnik

vbus_range_tab = [16, 32, 60, 60]
# Table converting config register BRNG field value to bus voltage range.
# The field value is an index to the table

vshunt_range_tab = [0.04, 0.08, 0.16, 0.32]
# Table converting config register PG field value to shunt voltage range.
# The field value is an index to the table.

conv_time_us_tab = [72, 132, 258, 508, 72, 132, 258, 508,
                    508, 1010, 2010, 4010, 8010, 16010, 32010, 64010]
# Table converting config register BADC and SADC field values to sample conversion times.
# The field value is an index to the table. The table values are expressed in microseconds


def set_config(brng, pg, badc, sadc, mode):
    ''' This function sets the DPM configuration register. It generates the config register value from
    the values of its fields: BRNG, PG, BADC, SADC and MODE. Then it writes the generated value
    into the config register. The config register field values are the arguments to the function.'''
    w = (brng << 13) | (pg << 11) | (badc << 7) | (sadc << 3) | mode
    # print(f'{w:x}')
    comm.send('wr 0 ' + format(w, 'x'))


def set_calibration(pg):
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
    vshuntfs = vshunt_range_tab[pg]
    w = int(1342.177 / vshuntfs)
    comm.send('wr 5 ' + format(w, 'x'))


def set_vshunt_threshold(minv, maxv):
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
    comm.send('wr 6 ' + format(w, 'x'))


def set_vbus_threshold(minv, maxv):
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
    comm.send('wr 7 ' + format(w, 'x'))


def read_bus_voltage(brng):
    ''' This function reads the bus voltage register and calculates the bus voltage
    It returns the bus voltage in volts (floating point value). It receives one argument,
    the value of the BRNG fieled of the config register - it expresses the bus voltage 
    range which is required for interpreting the bus voltage register value.'''
    comm.send('rr 2')
    resp = comm.response(removeCmd=True, returnAsList=False)
    w = int(resp, 16)
    if brng == 0:  # 16V (12 bits)
        w = (w >> 3) & 0x0fff
    elif brng == 1:  # 32V (13 bits)
        w = (w >> 3) & 0x1fff
    else:  # 60V (14 bits)
        w = (w >> 2) & 0x3fff
    voltage = float(w) * 0.004  # lsb = 4mV
    return voltage


def read_shunt_voltage(pg):
    ''' This function reads the shunt voltage register and calculates the shunt voltage
    It returns the shunt voltage in volts (floating point value). It receives one argument,
    the value of the PG fieled of the config register - it expresses the shunt voltage 
    range which is required for interpreting the shunt voltage register value.'''
    comm.send('rr 1')
    resp = comm.response(removeCmd=True, returnAsList=False)
    w = int(resp, 16)
    if pg == 0:
        sign_pos = 12
        tc = 4096
    elif pg == 1:
        sign_pos = 13
        tc = 8192
    elif pg == 2:
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


def read_current(pg, rshunt):
    ''' This function reads the current register and calculates the current.
    It returns the current in amps (floating point value). It receives two
    arguments which ar enecessary for the current calculation:
    - The value of the PG field of the config register representing the shunt voltage
      range (a.k.a. Vshunt full scale or VshuntFS)
    - The shunt resistor's resistance in Ohms.'''
    vshuntfs = vshunt_range_tab[pg]
    comm.send('rr 4')
    resp = comm.response(removeCmd=True, returnAsList=False)
    w = int(resp, 16)
    sign = (w >> 15) & 0x0001
    w = (w & 0x7fff) - (sign * 32768)
    currentfs = vshuntfs / rshunt
    currentlsb = currentfs / 32768
    cur = float(w) * currentlsb
    return cur


def read_power(pg, brng, rshunt):
    ''' This function reads the power register and calculates the power.
    It returns the power in watts in amps (floating point value). It receives two
    arguments which ar enecessary for the power calculation:
    - The value of the PG field of the config register representing the shunt voltage
      range (a.k.a. Vshunt full scale or VshuntFS)
    - The value of the BRNG field of the config register representing the bus voltage
      range (a.k.a. Vbus full scale or VbusFS)
    - The shunt resistor's resistance in Ohms.'''
    vshuntfs = vshunt_range_tab[pg]
    comm.send('rr 3')
    resp = comm.response(removeCmd=True, returnAsList=False)
    w = int(resp, 16)
    currentfs = vshuntfs / rshunt
    currentlsb = currentfs / 32768
    powerlsb = currentlsb * 0.004  # Vbus lsb = 4mV
    power = w * powerlsb * 5000
    if brng >= 2:  # implying VbusFS=60V
        power = power * 2
    return power


def get_threshold_int_status():
    ''' This function reads the interrupt status register and extracts the 4
    interrupt status bits. It returns an integer with these 4 interrupt bits:
    Bit 0 (BMNW): 1 indicates bus voltage below minimum 	
    Bit 1 (BMXW): 1 indicates bus voltage above maximum
    Bit 2 (SMNW): 1 indicates shunt voltage below minimum
    Bit 3 (SMXW): 1 indicates shunt voltage above maximum'''
    comm.send('rr 8')
    resp = comm.response(removeCmd=True, returnAsList=False)
    w = int(resp, 16) & 0xf
    return w


if __name__ == '__main__':

    comm = boardcom.BoardComm()   # create an instance of class BoardComm
    connectedPort = comm.find_and_connect(echo=1)
    du = dubrovnik.Dubrovnik()

    # dpm_ek_rshunt = 0.1 # Eval Kit shunt resistor value = 0.1Ohm
    dpm_ek_rshunt = 1.0  # Eval Kit shunt resistor value = 0.1Ohm

    config_brng = 0x0  # 16V
    config_pg = 0x1  # 80mV
    config_badc = 0x9  # 1.01ms
    config_sadc = 0xf  # 64.01ms
    config_mode = 0x7  # shunt & bus continuous
    set_calibration(config_pg)
    set_config(config_brng, config_pg, config_badc, config_sadc, config_mode)
    set_vshunt_threshold(0.02, 0.06)
    set_vbus_threshold(2, 4)

    print("### continouously read measurements for one minute ###")

    t_elapsed = 0
    t_start = time.time()

    while t_elapsed < 60.0:
        print("vbus = " + format(read_bus_voltage(config_brng), '.4f') + "V, ", end="")
        print("vshunt = " + format(read_shunt_voltage(config_pg), '.4f') + "V, ", end="")
        print("current = " + format(read_current(config_pg,
              dpm_ek_rshunt), '.4f') + "A, ", end="")
        print("power = " + format(read_power(config_pg,
              config_brng, dpm_ek_rshunt), '.4f') + "W, ", end="")
        ints = get_threshold_int_status()
        print("interrupt status = " + format(ints, '04b'))
        if ints != 0:
            comm.send("wr 8 f")
        time.sleep(2.0)
        t_elapsed = time.time() - t_start