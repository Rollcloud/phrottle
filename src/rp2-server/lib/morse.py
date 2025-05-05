import time

import machine

WPM = 15
CODE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "/": "--..-.",
    "@": ".--.-.",
    " ": " ",
}


def flash(led, t):
    #    led.low()
    #    time.sleep(t)
    led.high()
    time.sleep(t)
    led.low()
    return


def send(msg="SOS", pin="LED", wpm=WPM):
    led = machine.Pin(pin, machine.Pin.OUT)

    tdot = 1.2 / wpm
    tdash = tdot * 3
    tspace = tdot * 2
    tword = tdot * 6

    led.low()
    for letter in msg:
        code = CODE.get(letter.upper(), "")
        for each in code:
            if each == ".":
                flash(led, tdot)
                time.sleep(tdot)
            if each == "-":
                flash(led, tdash)
                time.sleep(tdot)
            if each == " ":
                time.sleep(tspace)
        time.sleep(tword)
    led.low()
