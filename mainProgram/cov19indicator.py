from machine import SPI, Pin
import network
import time
import ntptime

import gc

LOG_OUT = False
LOG_FILE = 'debug.log'
CASE_LOG = 'cases.log'
DUMMY_DATA = '20200913,22853,100'

# URL = "https://covid19-japan-web-api.now.sh/api/v1/total"
URL = "https://covid19-japan-web-api.now.sh/api/v1/prefectures"

######################### Display Config #######################
import ili9341
spi = SPI(miso=Pin(19), mosi=Pin(23, Pin.OUT), sck=Pin(18, Pin.OUT))
display = ili9341.ILI9341(spi, cs=Pin(14), dc=Pin(27), rst=Pin(33))
Pin(32, Pin.OUT).on()   # back light pin

COLOR565_INACTIVE = ili9341.color565(0xF0, 0xF0, 0xF0)
COLOR565_ACTIVE = ili9341.color565(0x40, 0x40, 0x40)

TEXT_X = 160
TEXT_Y = 120

######################### Update behaviour #######################
TIMESTAMP_OFFSET = 3 # 3: hour, 4: min
SLEEP_LENGTH_sec = 1
is_time_set = False

######################### Stepper Config #######################
# custom stepper driver
from a4988 import A4988

# pinconfig
stepPin = Pin(16)
dirPin = Pin(17)

stepper = A4988(stepPin, dirPin, 1000, 0, 0, pulse_width_us = 900, scale = 200)
stepper.wind(10)
stepper.wind(-10)

######################### Button Config #######################
btnA = Pin(39, Pin.IN, Pin.PULL_UP)
btnB = Pin(38, Pin.IN, Pin.PULL_UP)
btnC = Pin(37, Pin.IN, Pin.PULL_UP)

######################### WIFI connection sequence #######################
#  copied from here, TQ!
# https://garaemon.hatenadiary.jp/entry/2018/04/20/180000

def connect_wifi(target_ssid, target_passwd, timeout_sec=20):
    wlan = network.WLAN(network.STA_IF)  # create station interface
    wlan.active(True)                    # activate the interface
    if wlan.isconnected():
        return True

    for net in wlan.scan():
        ssid = net[0].decode()
        if ssid == target_ssid:
            print('Connecting to {}'.format(ssid))
            wlan.connect(ssid, target_passwd)
            start_date = time.time()
            while not wlan.isconnected():
                now = time.time()
                print('.', end = '')
                if now - start_date > timeout_sec:
                    break
                time.sleep(1)
            if wlan.isconnected():
                print('Succeed')
                return True
            else:
                print('Failed')
                return False
    return False


def check_connection():
    global is_time_set

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)                    # activate the interface
    if wlan.isconnected():
        return True
    is_time_set = False     # when the wifi connection is broken, unset time sync flag
    return False

def connect_network():
    try:
        f = 0
        # if ENABLE_SD:
        #     # recursively lead wifi ssid and password from wifi.ini file on sd
        #     f = open('/sd/wifi.ini')
        # else:
        # f = open('wifi.ini')
        if(not check_connection()):
            with open('wifi.ini') as f:
                wifi_info = f.readline()
                while wifi_info != '':
                    ssid = wifi_info.split(',')[0]
                    pw = wifi_info.split(',')[1][:-2]
                    if connect_wifi(ssid, pw):
                        f.close()
                        print("connected")
                        return True
                        # break
                    else:
                        print("connection failed: {0}".format(ssid))
                    # wait(1)
                    time.sleep_ms(1)
                    wifi_info = f.readline()
        else:
            print("already online")
            return True
    except Exception as e:
        print("No wifi.ini file")
        debug_log("connection unsuccessful")
        return False
    return False
########################### Time update using NTP #####################################
def set_networktime():
    global is_time_set

    if check_connection():
        if is_time_set:
            return True
        else:
            try:
                ntptime.settime()

                print("time set")
                is_time_set = True
                return True

            except Exception as e:
                debug_log("ntp error:{}".format(e))

    return False
########################### Flash logger function #####################################
def debug_log(msg):
    if LOG_OUT:
        currentTime = time.localtime()
        logdata = "{0}.{1}.{2} {3}:{4}:{5} {6}\n".format(
            currentTime[0], currentTime[1], currentTime[2], currentTime[3], currentTime[4], currentTime[5], msg)
        print(logdata)
        with open(LOG_FILE, 'a') as f:
            f.write(logdata)
    return

################## Data fetch fucntion using sockets #####################################
def updatePic_sockets(url):
    # debug_timeCounter_last_ms = time.ticks_ms()
    import usocket as socket

    rcv_data = bytearray()

    proto, dummy, host, path = url.split('/', 3)
    # print(URL)
    # print('proto: ' + str(proto))
    # print('dummy: ' + str(dummy))
    # print('host: ' + str(host))
    # print('path: ' + str(path))

    port = 80
    if proto == 'https:':
        port = 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    addr = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)[0][-1]

    s = socket.socket()
    method = "GET"

    try:
        s.connect(addr)
        if proto == "https:":
            import ussl
            s = ussl.wrap_socket(s, server_hostname=host)
        s.write(b"%s /%s HTTP/1.0\r\nHost: %s\r\n\r\n" %
                (method, path, host))
        header_counter = 0
        header_received = False
        while True:
            # buffer size should not exceed header + content size!
            data = s.read(256)
            if data:
                # print(data)
                # data will be splitted with \r\n\r\n\ = CR LF CR LF
                l = split_list(data, [13, 10, 13, 10])

                # when found "\r\n\r\n", it indicates the end of the header, so store the rest and proceed for the data receive process
                if len(l) == 2:
                    # print("header= : {} ".format(len(l[0])))
                    # print(l[0])
                    # print("content= : {}\n".format(len(l[1])))
                    rcv_data += l[1]
                    header_received = True
                    break
            if header_counter > 2:
                rcv_data = bytearray()  # clear the data
                break
            header_counter += 1
        # once you received header and parsed out, receive 100 bytes data per each step until it stops.
        while header_received:
            data = s.read(1024)

            if data:
                # print(data)
                print(".", end='')
                rcv_data += data

            # When no data is available, suppose all data were received. finish the loop...
            else:
                print("Data received\n")
                break
    except Exception as e:
        print("Error: {0}\n".format(e))
        rcv_data = bytearray()      # Clean up data when the data transfer is incomplete
        print("GC freemem: {0}\n".format(gc.mem_free()))
        debug_log("data not received")

    s.close()
    gc.collect()  # garbage collector
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

    # debug_delta('fetch data')
    return rcv_data

########################## Data getter ######################################
def split_list(l, s):
    count = 0
    ni = []
    for i in range(0, len(l)-len(s)):
        if l[i] == s[count]:
            count = count+1
            if count == len(s):
                # lcd.println("Matched")
                ni.append(i+1)
                count = 0
        else:
            count = 0
    if len(ni) == 0:
        return l
    else:
        r = []
        pi = 0
        for j in range(0, len(ni)):
            r.append(l[pi:(ni[j]-len(s))])
            pi = ni[j]
        r.append(l[pi:len(l)])
        return r

########################## Parse JSON and extract data from Tokyo ##################
def extract_tokyo_data(dataStream):
    # infection_data_str = str(dataStream)[12:-2]
    infection_data_str = dataStream.decode()
    dataStream = ""

    gc.collect()  # garbage collector
    # gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

    infection_data = infection_data_str.split('},\n  {')
    if len(infection_data) == 47:   #Tokyo's data is 47th in JSON
        import ujson
        return ujson.loads('{' + infection_data[12] + '}')
    else:
        return ""

def write_dummy_data():
    d = open('cases.log', 'w')
    d.write(DUMMY_DATA)     # dummy data
    d.close()
    return

########################## Check daily infections and compares to the log data ##################
def update_daily_infections(date, cases):
    print("incoming data: {}, {}".format(date, cases))
    dailyCases = 0
    import os
    if CASE_LOG in os.listdir():
        with open(CASE_LOG, 'r+') as f:
            cases_text = f.readline()
            if len(cases_text.split(',')) == 3:
                date_log, cases_log, dailyCases_log = cases_text.split(',')
                print("log: {}, {}, {}".format(date_log, cases_log, dailyCases_log))
                cases_log = int(cases_log)
                date_log = int(date_log)
                dailyCases_log = int(dailyCases_log)
                dailyCases = dailyCases_log

                # when log file date or case have changed, updates logfile data
                if (date != date_log) or (cases != cases_log):
                    print("updated log file: {}, {}".format(date, cases))
                    
                    if cases >= cases_log:
                        dailyCases = cases - cases_log
                        if date == date_log:
                            dailyCases += dailyCases_log    
                    # save new data
                    f.seek(0)
                    f.write(str(date) + ',' + str(cases) + ',' + str(dailyCases))
    # if there is no log file available
    else:
        write_dummy_data()
        dailyCases = 100
    print("daily cases: {}".format(dailyCases))
    return dailyCases

################## Update function ###########################
def check_update():
    display.fill(COLOR565_ACTIVE)
    gc.collect()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

    if connect_network():
        if set_networktime():            
            infection_data = extract_tokyo_data(updatePic_sockets(URL))

            gc.collect()  # garbage collector
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

            # print(type(infection_data))
    #         print(infection_data['cases'])
    #         print(infection_data['last_updated']['cases_date'])
            dailyInfections = update_daily_infections(
                infection_data['last_updated']['cases_date'], infection_data['cases'])
            
            display.fill(COLOR565_INACTIVE)
            display.text(str(dailyInfections), TEXT_X, TEXT_Y, color = 0x0, background = COLOR565_INACTIVE)
            stepper.moveto(dailyInfections)

    gc.collect()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

################## Handling button input #########################
def check_button_events():
    # wind down
    if btnA.value() == 0:
        while btnA.value() == 0:
            stepper.wind(1)

    # get new data
    if btnB.value() == 0:
        check_update()

    # wind up
    if btnC.value() == 0:
        while btnC.value() == 0:
            stepper.wind(-1)
    return

################### init sequence ##################################
display.fill(COLOR565_INACTIVE)
timeStamp = time.localtime()[TIMESTAMP_OFFSET] -1 #extract hour

########################### Main loop ################################
while(1):

    check_button_events()

    if time.localtime()[TIMESTAMP_OFFSET] != timeStamp:
        timeStamp = time.localtime()[TIMESTAMP_OFFSET]  #extract hour
        print("updating...")
        check_update()
    else:
        print(".", end = "")
    time.sleep(SLEEP_LENGTH_sec)
    
