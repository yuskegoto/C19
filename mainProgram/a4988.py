from machine import Pin
from time import sleep_us

# stepPin = Pin(16)
# dirPin = Pin(17)

class A4988:
    def __init__(self, step_pin, dir_pin, halt_pin, maxpos, minpos, init_pos, pulse_width_us = 1000, scale = 100):
        self.maxpos = maxpos
        self.minpos = minpos
        self.pos = init_pos
        self.step = step_pin
        self.step.init(self.step.OUT, value= 0)
        self.dir = dir_pin
        self.dir.init(self.dir.OUT, value= 0)
        self.scale = scale #steps per unit
        self.pulseWidth = pulse_width_us
        self.haltPin = halt_pin
        return

    #move stepper to specified position and inclement motor position
    def moveto(self, nextPos):
        if nextPos > self.maxpos:
            nextPos = self.maxpos
        elif nextPos < self.minpos:
            nextPos = self.minpos

        if nextPos > self.pos:
            self.dir.on()
        else:
            self.dir.off()
        moveSteps = abs(nextPos - self.pos) * self.scale
        for i in range(moveSteps):
            self.onePulse()
            if self.haltPin.value() == 0:
                break
        self.pos = nextPos
        return

    #move stepper but not inclement motor position    
    def wind(self, inclement):
        if inclement > 0:
            self.dir.on()
        else:
            self.dir.off()

        moveSteps = abs(inclement - self.pos)
        for i in range(moveSteps):
            self.onePulse()
            break
        return

    def onePulse(self):
        self.step.on()
        sleep_us(self.pulseWidth)

        self.step.off()
        sleep_us(self.pulseWidth)
        return

# stepper = A4988(stepPin, dirPin, 100, 0, 0)
# # while(1):
# stepper.moveto(100)
# print(stepper.pos)
# stepper.moveto(0)