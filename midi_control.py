#!/usr/bin/python

import pygame
import pygame.midi as midi


class Event(object):
    NOTE_ON = 144
    NOTE_OFF = 128


class Note(object):
    C = 0
    Csharp = Dflat = 1
    D = 2
    Dsharp = Eflat = 3
    E = 4
    F = 5
    Fsharp = Gflat = 6
    G = 7
    Gsharp = Aflat = 8
    A = 9
    Asharp = Bflat = 10
    B = 11


class TerminateOnSuccess(Exception):
    """
    Exception for ending MIDI input upon successful melody
    """
    pass


class BaseMelody():
    def __init__(self, melody, name=None):
        self.melody = melody
        self.index = 0
        self.name = name

    def match_pitch(self, pitch):
        if pitch == self.melody[self.index]:
            self.index += 1
            if self.index == len(self.melody):
                self._success()
                self.index = 0
        else:
            self.index = 0
            self._fail()

    def _success(self):
        raise NotImplementedError

    def _fail(self):
        pass


class PrintMelody(BaseMelody):
    def _success(self):
        print "Success! %s" % self.name


class TerminalMelody(BaseMelody):
    def _success(self):
        raise TerminateOnSuccess(self.name)


class KeyBoard():

    def __init__(self, input_device_id, melodies, output_device_id=None):
        self.midi_input = midi.Input(input_device_id)
        self.midi_output = None
        if output_device_id is not None:
            self.midi_output = midi.Output(output_device_id, buffer_size=8, latency=1)

        self.matched_index = 0
        self.melodies = melodies

    def start(self):
        while True:
            if self.midi_input.poll():
                bytes, time = self.midi_input.read(1)[0]
                if self.midi_output:
                    self.midi_output.write([[bytes, time]])

                try:
                    self._process_bytes(bytes, time=time)
                except TerminateOnSuccess as e:
                    print "Terminating due to success of: %s" % e
                    return

    def _process_bytes(self, bytes, time=None):
        event = bytes[0]
        pitch = bytes[1]
        intensity = bytes[2]

        if event == Event.NOTE_ON:
            self._match_melodies(pitch % 12)

    def _match_melodies(self, pitch):
        for melody in self.melodies:
            melody.match_pitch(pitch)


def main():
    pygame.init()
    midi.init()
    default_input_device = midi.get_default_input_id()
    default_output_device = midi.get_default_output_id()

    if default_input_device < 0:
        print "No MIDI input device found"
        return

    melodies = []

    # Gary Jules - Mad World
    melody = [Note.Gsharp, Note.C, Note.G, Note.Gsharp, Note.F, Note.G, Note.Dsharp, Note.D]
    melodies.append(
        PrintMelody(melody, name="Mad World")
    )

    # Happy birthday
    melody = [Note.D, Note.D, Note.E, Note.D, Note.G, Note.F]
    melodies.append(
        TerminalMelody(melody, name="Happy Birthday")
    )

    keyboard = KeyBoard(default_input_device, melodies, output_device_id=default_output_device)

    print "Initialized"
    keyboard.start()

if __name__ == "__main__":
    main()
