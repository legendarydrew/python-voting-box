# Pico Voting Booth
# developed from scratch by Drew Maughan (SilentMode).

# ---------------------------------------------------
# OBJECTIVES
# + set up buttons for voting.
# + light up the corresponding LED when a button is pressed.
# + record the chosen vote to a file on an SD card.
# + sound a buzzer when the vote is recorded.
# + display "breathing" LEDs while idle.
# - a test switch (testing the ability to vote).
# - a shutdown button.
# ---------------------------------------------------

from machine import Pin, PWM, SPI
import math
import sdcard
import time
import uos

# Voting buttons (input).
btnVoteA = Pin(2, Pin.IN, Pin.PULL_UP)
btnVoteB = Pin(3, Pin.IN, Pin.PULL_UP)
btnVoteC = Pin(4, Pin.IN, Pin.PULL_UP)

# Shutdown button (input).
btnShutdown = Pin(19, Pin.IN, Pin.PULL_UP)

# Buzzer (output).
buzzer = Pin(0, Pin.OUT)
buzzer.value(0)

# Corresponding LEDs (output).
# These are set up with Pulse Width Modulation (PWM) for "breathing" LEDs.
ledVoteA = PWM(Pin(15))
ledVoteB = PWM(Pin(17))
ledVoteC = PWM(Pin(16))
leds = [ledVoteA, ledVoteB, ledVoteC]

ledCount = 0
ledStep = []

breatheGap = 48 # 12
breatheSpeed = 0.5
breatheMaxDuty = 16384 # maximum 65535 (full brightness)

PI = 3.14 # one more one false move and they're done for...

def setupSDCard():
    # Memory card (using CS pin).
    cs = Pin(9, Pin.OUT)
    spi = SPI(1,
          baudrate=1000000,
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(10),
          mosi=Pin(11),
          miso=Pin(8))
    sd = sdcard.SDCard(spi, cs)

    # Mount the filesystem.
    vfs = uos.VfsFat(sd)
    try:
        uos.mount(vfs, '/sd')
    except OSError as e:
        print('OS Error', e)

def setupLEDs():
    global ledCount
    ledCount = len(leds)
    for index in range(ledCount):
        leds[index].freq(10000)
        ledStep.append(index * -breatheGap)

# Performs a single step in having the LEDs "breathe" (fade in and out).
def breathe():
    for index in range(ledCount):
        ledStep[index] += breatheSpeed
        if (ledStep[index] >= 360):
            ledStep[index] = ledStep[index] % 360

        brightness = 0
        if ( ledStep[index] >= 0 ):
            brightness = abs(math.sin(ledStep[index] * PI / 180)) * breatheMaxDuty

        leds[index].duty_u16(int(brightness))

# Turn off and deinitialise the LEDs.
def turnOffLEDs():
    for index in range(ledCount):
        leds[index].duty_u16(0)
        leds[index].deinit()
        
# Record a vote for the specified option.
def castVote(button, led, value):
    # Turn off all the LEDs, reset counters.
    for index in range(ledCount):
        leds[index].duty_u16(0)
        ledStep[index] = 0
        
#     print("Cast vote for ", value)
    print(value,end="") # consnecutive votes on the same line.
  
    # Turn on the corresponding button's LED.
    led.duty_u16(65535)
  
    # Don't do anything else while the button is held down.
    while not button.value():
        time.sleep_ms(20)
    
    # Turn the LED off.
    led.duty_u16(0)
    
    # Append the vote to a text file.
    with open('/sd/votes.txt', 'a') as file:
        file.write(value)
        file.close()
     
    # Sound the buzzer.
    buzzer.value(1)
    time.sleep_ms(300)
    buzzer.value(0)
    
    # Reset the LED steps.
    for index in range(ledCount):
        ledStep[index] = index * -breatheGap
  
def shutdown():
    print("!")
    uos.umount('/sd')
    turnOffLEDs()
    for index in range(6):
        buzzer.value(0.2)
        time.sleep_ms(50)
        buzzer.value(0)
        time.sleep_ms(50)

# ------------------------------------------------------------------

setupSDCard()
setupLEDs()

try:    
    print('Voting Booth ready.')
    while True:
        if not btnShutdown.value():
            shutdown()
            break
        if not btnVoteA.value():
            castVote(btnVoteA, ledVoteA, "A")
        if not btnVoteB.value():
            castVote(btnVoteB, ledVoteB, "B")
        if not btnVoteC.value():
            castVote(btnVoteC, ledVoteC, "C")
        breathe()        
        time.sleep_ms(20)
except e:
    print('Program Error', e)
    shutdown()
    pass
