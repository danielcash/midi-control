#!/usr/bin/python
import pygame
import pygame.midi as midi

from midi_control import KeyBoard, Note


def formatted_print_chords(chords):
    output = []
    for chord in chords:
        chord_list = list(chord)
        if len(chord_list) == 1:
            output.append("Note.%s" % Note.note_from_index(chord_list[0]))
        elif len(chord_list) > 1:
            pitches = [("Note.%s" % Note.note_from_index(chord)) for chord in chord_list]
            output.append("{%s}" % ", ".join(pitches))
    return "[%s]" % ", ".join(output)


class ChordBuilderKeyBoard(KeyBoard):
    saved_pitches = []
    def _chord_callback(self, pitches):
        self.saved_pitches.append(pitches)

    def _process_other_events(self, bytes, time):
        if self.saved_pitches:
            print formatted_print_chords(self.saved_pitches)
            self.saved_pitches = []


def main():
    pygame.init()
    midi.init()
    default_input_device = midi.get_default_input_id()
    default_output_device = midi.get_default_output_id()

    if default_input_device < 0:
        print "No MIDI input device found"
        return

    melodies = []

    keyboard = ChordBuilderKeyBoard(default_input_device, melodies, output_device_id=default_output_device)

    print "Initialized"
    keyboard.start()


if __name__ == "__main__":
    main()
