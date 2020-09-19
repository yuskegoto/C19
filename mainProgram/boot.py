# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
try:
    import cov19indicator
# when something happens, write out error status and try to reboot
except Exception as e:
    import time
    with open('debug.log', 'a') as f:
        currentTime = time.localtime()
        logdata = "{0}.{1}.{2} {3}:{4}:{5} {6}\n".format(currentTime[0], currentTime[1], currentTime[2], currentTime[3], currentTime[4], currentTime[5], e)
        f.write(logdata)
        import machine
        machine.reset()