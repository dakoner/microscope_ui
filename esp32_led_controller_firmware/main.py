# See https://www.mindvision.com.cn/wp-content/uploads/2023/12/MV-QR-CP-19-0090-MV-SUA34GC-M-A0.pdf for wiring details of camera
import sys
import utime
import esp32

from machine import Pin, PWM
from machine import Timer

TRIGGER_PIN=23
STROBE_PIN=22
LED_PIN=23
class Program():
    def __init__(self):
        self.pwm = None
        self.rmt = None

        # # # # Camera trigger
        # self.trigger = Pin(TRIGGER_PIN, Pin.OUT, Pin.PULL_DOWN)
        # self.trigger.off()

        # # # # Camera strobe
        # self.strobe = Pin(STROBE_PIN, Pin.IN)
        # self.strobe.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=self.handle)

        self.led = Pin(LED_PIN)
        self.led.init(mode=Pin.OUT)
        self.led.off()

    def cb(self, timer):
        self.led.off()

    def handle(self, pin):
        if pin.value():
           self.led.off()
           print("rising")
        else:
           self.led.on()
           print("falling")
        #self.tim0.init(period=1000, mode=Timer.ONE_SHOT, callback=self.cb)
        # if not pin.value():
        #     self.rmt = esp32.RMT(0, pin=self.led, clock_div=64) # 1 time unit = 3 us
        #     self.rmt.write_pulses((32767,), 1)  # Send HIGH for 32767 * 100ns = 3ms
        # else:
        #     self.rmt.deinit()


    def loop(self):
        while True:
            try:
                sys.stdout.write('scopie:> ')
                line = input()
                if line.startswith('L'):
                    #self.led.init(mode=Pin.OUT)
                    s = line.split(' ')
                    b = bool(int(s[1]))
                    if b:
                        print("led on")
                        self.led.on()
                    else:
                        print("led off")
                        self.led.off()
                elif line.startswith('P'):
                    s = line.split(' ')
                    freq = int(s[1])
                    duty = int(s[2])
                    pwm = PWM(self.led, freq=freq, duty=duty)
                    print(pwm)
                # elif line.startswith('Q'):
                #     rmt = esp32.RMT(0, pin=Pin(LED_PIN), clock_div=1) # 1 time unit = 3 us
                #     rmt.write_pulses((10,), 1)
                #     rmt.wait_done()
                #     rmt.deinit()
                # elif line.startswith('D'):
                #     dac = DAC(Pin(25))
                #     s = line.split(' ')
                #     v = int(s[1])
                #     dac.write(v)
                # elif line.startswith('S'):
                #     self.led.init(mode=Pin.OUT)
                #     s = line.split(' ')
                #     self.led.off()
                #     delay = int(s[1])
                #     print("light up and sleep for", delay)
                #     self.led.on()
                #     utime.sleep_us(delay)
                #     self.led.off()
                elif line.startswith('C'):
                    s = line.split(' ')
                    self.trigger.off()
                    utime.sleep_ms(10)
                    delay = int(s[1])
                    print("trigger camera for", delay)
                    self.trigger.on()
                    #utime.sleep_us(delay)
                    utime.sleep_ms(delay)
                    self.trigger.off()
                # elif line.startswith('N'):
                #     s = line.split(' ')
                #     b = bool(int(s[1]))
                #     if b:
                #         print("trigger on")
                #         self.trigger.on()
                #     else:
                #         print("trigger off")
                #         self.trigger.off()
                else:
                    print("Unknown: ", line)
            except Exception as e:
                print(str(e))

p = Program()
print("Version 0.2")
p.loop()
