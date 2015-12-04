#!/usr/bin/python

import pygame
import pygame.midi as midi


MIN_TIME_FOR_CHORD = 100  # ms


class Event():
    NOTE_ON = 144
    NOTE_OFF = 128


class Note():
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

    _lookup_list = ["C", "Csharp", "D", "Dsharp", "E", "F", "Fsharp", "G", "Gsharp", "A", "Asharp", "B"]

    @classmethod
    def note_from_index(cls, index):
        return cls._lookup_list[index]


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

    def match_pitch(self, chord):
        """
        Match incoming chord/pitch with the given melody

        :type chord: set
        :chord: set of unique pitches
        """
        if len(chord) == 1:
            chord = list(chord)[0]
        if chord == self.melody[self.index]:
            self.index += 1
            if self.index == len(self.melody):
                self._success()
                self.index = 0
        else:
            self.index = 0
            self._fail()

    def _success(self):
        """
        Defines what action is taken when a melody is played successfully

        Must be overridden by subclass
        """
        raise NotImplementedError

    def _fail(self):
        """
        Defines what action is taken when a melody is played unsuccessfully

        By default, does nothing. When there are multiple melodies available,
        having a failure case for each one is not a good idea
        """
        pass


class PrintMelody(BaseMelody):
    def _success(self):
        print "Success! %s" % self.name


class TerminalMelody(BaseMelody):
    def _success(self):
        raise TerminateOnSuccess(self.name)


class KeyBoard():

    def __init__(self, input_device_id, melodies, output_device_id=None):
        self.melodies = melodies
        self.midi_input = midi.Input(input_device_id)
        self.midi_output = None
        if output_device_id is not None:
            self.midi_output = midi.Output(output_device_id, buffer_size=8, latency=1)

        self.pitches = {}
        self.continue_processing = True

    def start(self):
        """
        Begin processing MIDI input
        """
        while True:
            if self.midi_input.poll():
                bytes, time = self.midi_input.read(1)[0]
                if self.midi_output:
                    self.midi_output.write([[bytes, time]])

                try:
                    self._process_bytes(bytes, time)
                except TerminateOnSuccess as e:
                    print "Terminating due to success of: %s" % e
                    return

    def _process_bytes(self, bytes, time):
        """
        Decode MIDI event, filter chords, and call melody matching

        TODO: refactor this method - it's doing too much
        """
        event = bytes[0]
        pitch = bytes[1] % 12
        intensity = bytes[2]
        pitches = self.pitches

        if event == Event.NOTE_ON:
            self.pitches[pitch] = time
            self.continue_processing = True
        elif event == Event.NOTE_OFF:
            if self.continue_processing:
                pitches = self._filter_chords(pitches, pitch, time)
                if pitches:
                    # print "pitches: %s" % pitches
                    self._match_melodies(pitches)
                    self._chord_callback(pitches)
            if pitch in self.pitches:
                del self.pitches[pitch]
        else:
            self._process_other_events(bytes, time)

    def _filter_chords(self, pitches, current_pitch, current_time):
        """
        Filters out extraneous pitches from chords

        If there is only one pitch in `pitches`, process that pitch regardless of time span
        If there are more than one pitch in `pitches`, process only the pitches that have existed
            longer than MIN_TIME_FOR_CHORD
        If the pitch that triggered the processing was filtered out, stop processing `pitches`
            - this likely means an extraneous pitch was quickly hit and released during a chord
        """
        if len(pitches) == 1:
            self.continue_processing = True
            return set(pitches.keys())

        self.continue_processing = False
        filtered_pitches = set()
        for pitch in pitches.keys():
            if current_time - pitches[pitch] >= MIN_TIME_FOR_CHORD:
                filtered_pitches.add(pitch)
        if len(filtered_pitches) != len(pitches):
            self.continue_processing = True
        if current_pitch not in filtered_pitches:
            return None
        return filtered_pitches

    def _match_melodies(self, pitches):
        """
        Look for matching pitches/chords in the list of available melodies
        """
        for melody in self.melodies:
            melody.match_pitch(pitches)

    def _chord_callback(self, pitches):
        """
        Callback that can overridden by subclass to do something with a complete chord/pitch
        """
        pass

    def _process_other_events(self, bytes, time):
        """
        Handler for MIDI events other than NOTE-ON and NOTE-OFF that can be overriden by subclass
        """
        pass


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
    melody = [Note.Gsharp, Note.C, Note.G, Note.Gsharp, Note.F, Note.G, Note.Dsharp, Note.D, Note.Gsharp, Note.C, Note.G, Note.Gsharp, Note.F, Note.G, Note.Gsharp, Note.Asharp]
    melodies.append(
        PrintMelody(melody, name="Mad World")
    )

    # Happy birthday
    melody = [Note.D, Note.D, Note.E, Note.D, Note.G, Note.F]
    melodies.append(
        TerminalMelody(melody, name="Happy Birthday")
    )

    # Chord example
    melody = [
        {Note.C, Note.E, Note.G},  # C Major Chord
        Note.D,
        {Note.F, Note.Aflat, Note.C},  # F Minor Chord
        Note.D
    ]
    melodies.append(
        PrintMelody(melody, name="Chord Example")
    )

    keyboard = KeyBoard(default_input_device, melodies, output_device_id=default_output_device)

    print "Initialized"
    keyboard.start()

if __name__ == "__main__":
    main()
