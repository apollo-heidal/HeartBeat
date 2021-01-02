''' 
Gets HR and ACC data from H10.

Written by Apollo Heidal
'''

import asyncio
from time import time
from bleak.backends.bluezdbus.client import BleakClientBlueZDBus

H10_MAC_ADDR = 'EA:ED:67:25:A1:03'
CLIENT = BleakClientBlueZDBus(H10_MAC_ADDR)

# relevant H10 service/characteristic/descriptor UUIDs
PMD_CONTROL_POINT_CHAR_UUID = 'fb005c81-02e7-f387-1cad-8acd2d8df0c8'
PMD_DATA_MTU_CHAR_UUID = 'fb005c82-02e7-f387-1cad-8acd2d8df0c8'
HR_MEASUREMENT_CHAR_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

# byte array opcodes
GET_ECG_SETTINGS_OP_CODE = bytearray([0x01, 0x00])
GET_ACC_SETTINGS_OP_CODE = bytearray([0x01, 0x02])
START_ECG_MEASUREMENT_OP_CODE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0e, 0x00])
STOP_ECG_MEASUREMENT_OP_CODE = bytearray([0x03, 0x00])

def controlPointResponseHandler(sender, data):
    print("data from 0x{:02x}:".format(sender))
    print("".join(" {:02x}".format(x) for x in data))
    '''assert(sender == 0x46)
    try:
        assert(data[3] == 0x00)
    except AssertionError:
        print("Exception! error code is {:02x}".format(data[3]))
                
    print("data from 0x{:02x}:".format(sender))
    print("\tcontrol point response:")
    
    if data[1] == 0x01: # op_code(Get Measurement settings)
        print("\t\tmeasurement settings")
    '''

samples = dict()

def dataResponseHandler(sender, data):
    '''
    ECG stream packet is little endian with following format:
        [0] == 0x00
        [1:9] == timestamp of last sample (ns)
        [9] == 0x00 (ECG frameType; 3B uV)
        [10::3] == data frames
    '''
    # double check sender and correct packet format
    assert(sender == 0x49)
    assert(len(data[10:]) % 3 == 0)

    ## debug statements
    # print("data(len={:d}) from ".format(len(data)), end="")
    # if data[0] == 0x00:
    #     print("ECG:")
    # elif data[0] == 0x02:
    #     print("ACC:")

    timestamp = int.from_bytes(data[1:9], byteorder='little') #nanoseconds
    samples[timestamp] = []
    ## print("timestamp: {:d}".format(timestamp))

    # ECG frames are 3B in little endian
    for frame in range(10, len(data[10:]) + 10, 3):
        #print("0x" + "".join("{:02x}".format(x) for x in data[frame:frame+3]), end=" ")
        uV = int.from_bytes(data[frame:frame+3], byteorder="little", signed=True)
        # print(uV)
        samples[timestamp].append(uV)

    # print(samples[timestamp])
    # print()


def formatAndSave():
    times = sorted(samples.keys())
    start_time = times[0] - (times[1] - times[0]) # approximate t0: t0 = t1 - (t2 - t1)
    end_time = times[-1]

    with open("samples.csv", "w") as fileHandler:
        # iterate over all the timestamps
        for t in range(1, len(times)):
            # iterate through samples are approximate time based on timestamp[t-1] and timestamp[t]
            this_packet = samples[times[t]]
            for s in enumerate(this_packet):
                if t == 1: #first packet
                    s_time = ((times[t] - start_time) / len(this_packet)) * s[0]
                    fileHandler.write("{:d},{:d}\n".format(int(s_time), s[1]))
                else: #all other packets
                    s_time = (((times[t] - times[t-1]) / len(this_packet)) * s[0]) + (times[t-1] - start_time)
                    fileHandler.write("{:d},{:d}\n".format(int(s_time), s[1]))
            #print("time diff: {:d}".format(times[t] - times[t-1]))


async def main():
    # connect to H10
    if not await CLIENT.is_connected():
        await CLIENT.connect()

    # start notifications on PMD control point and data chars
    print("Start PMD control point notify...")
    await CLIENT.start_notify(PMD_CONTROL_POINT_CHAR_UUID, controlPointResponseHandler)
    print("Start PMD data notify...")
    await CLIENT.start_notify(PMD_DATA_MTU_CHAR_UUID, dataResponseHandler)

    # request ecg stream settings from control point
    print("Request ECG stream settings from PMD control point...")
    await CLIENT.write_gatt_char(PMD_CONTROL_POINT_CHAR_UUID, GET_ECG_SETTINGS_OP_CODE)
    #await CLIENT.write_gatt_char(PMD_CONTROL_POINT_CHAR_UUID, GET_ACC_SETTINGS_OP_CODE)

    # request start ecg stream from data MTU
    print("Start ECG data stream...")
    await CLIENT.write_gatt_char(PMD_CONTROL_POINT_CHAR_UUID, START_ECG_MEASUREMENT_OP_CODE)
    
    await asyncio.sleep(20)

    # request stop ecg stream
    await CLIENT.write_gatt_char(PMD_CONTROL_POINT_CHAR_UUID, STOP_ECG_MEASUREMENT_OP_CODE)

    await asyncio.sleep(1)

    if await CLIENT.is_connected():
        await CLIENT.disconnect()

    formatAndSave()

asyncio.run(main())

