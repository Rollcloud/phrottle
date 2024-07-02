import math
from machine import Pin, PWM
import utime

TWO_PI = math.pi * 2
SAMPLING_RATE = 16000  # Hz
TICK = 1 / SAMPLING_RATE

speaker_pos = None
speaker_neg = None

NOTES = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]


def pitch2freq(pitch, A4=440):
    note = NOTES.index(pitch[:-1])
    octave = int(pitch[-1])
    distance_from_A4 = note + 12 * (octave - (4 if note < 3 else 5))

    return A4 * 2 ** (distance_from_A4 / 12)


def chord(pitches):
    return [int(pitch2freq(pitch)) for pitch in pitches]


def init():
    global speaker_pos, speaker_neg
    speaker_pos = PWM(Pin(6, Pin.OUT))
    speaker_neg = PWM(Pin(9, Pin.OUT))
    speaker_pos.freq(SAMPLING_RATE * 2)
    speaker_neg.freq(SAMPLING_RATE * 2)


def _play_level(level: float):
    global speaker_pos, speaker_neg
    amplitude = int(abs(level * 65535))
    if level > 0:
        speaker_neg.duty_u16(0)
        speaker_pos.duty_u16(amplitude)
    else:
        speaker_pos.duty_u16(0)
        speaker_neg.duty_u16(amplitude)


def off():
    global speaker_pos, speaker_neg
    speaker_pos.deinit()
    speaker_neg.deinit()


def t():
    return utime.ticks_us()


def play(sample):
    _play_level(sample)
    utime.sleep(TICK)


# init()

# try:
#     freq = 440
#     while True:
#         wave = math.sin(t() * TWO_PI * freq)
#         play(wave)
# except KeyboardInterrupt:
#     off()
# except Exception:
#     off()
