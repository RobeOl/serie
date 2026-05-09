from music21 import *
import random
import copy

def f_octave(x, ottave, oct):
    if (ottave == 1) and (x.octave >= (oct+2)):
        x.octave=oct
    elif (ottave == 2) and (x.octave >= (oct+3)):
        x.octave = oct


def f_durata(x):
    x.duration.quarterLength = random.choice([1, 1/2, 1/4])

def genera_ternary(tipo,note_len,i,j,k,ottave,bass_clef,starting_note,harmony,harmony_type):
	c = note.Note(starting_note)

	if starting_note <= 6:
		c.octave = 4
	else:
		c.octave = 3

	oct = c.octave

	notes = []

	# first interval, starting with C4
	note1 = c

	if tipo=="sequence-constrained":
		# sequence-constrained
	
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		first_note = note1.name

		# first axis
		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# second axis
		note1.transpose(j,inPlace=True)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# third axis
		note1.transpose(k,inPlace=True)
		f_octave(note1,ottave, oct)
		f_durata(note1)
		notes.append(copy.deepcopy(note1))

		current_note = note1.name
		condition = (current_note!=first_note)

		# begin repetition
		while condition:
			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave, oct)
			notes.append(copy.deepcopy(note1))

			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave, oct)
			notes.append(copy.deepcopy(note1))

			note1.transpose(k,inPlace=True)
			f_octave(note1,ottave, oct)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))
			current_note = note1.name
			condition = (current_note!=first_note)

	elif tipo=="length-constrained":
		conta = 1
		note_number = random.choice([2,3,5,6])

		# length constrained
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		first_note = note1.name

		# first axis
		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave, oct)
		if conta==note_number:
			f_durata(note1)
			conta=1
		else:
			conta = conta+1
		notes.append(copy.deepcopy(note1))

		# second axis
		note1.transpose(j,inPlace=True)
		f_octave(note1,ottave, oct)
		if conta==note_number:
			f_durata(note1)
			conta=1
		else:
			conta = conta+1
		notes.append(copy.deepcopy(note1))

		# third axis
		note1.transpose(k,inPlace=True)
		f_octave(note1,ottave, oct)
		if conta==note_number:
			f_durata(note1)
			conta=1
		else:
			conta = conta+1
		notes.append(copy.deepcopy(note1))

		current_note = note1.name
		condition = (current_note!=first_note)

		# begin repetition
		while condition:
			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave, oct)
			if conta==note_number:
				f_durata(note1)
				conta=1
			else:
				conta = conta+1
			notes.append(copy.deepcopy(note1))

			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave, oct)
			if conta==note_number:
				f_durata(note1)
				conta=1
			else:
				conta = conta+1
			notes.append(copy.deepcopy(note1))

			note1.transpose(k,inPlace=True)
			f_octave(note1,ottave, oct)
			if conta==note_number:
				f_durata(note1)
				conta=1
			else:
				conta = conta+1
			notes.append(copy.deepcopy(note1))
			current_note = note1.name
			condition = (current_note!=first_note)

	elif tipo=="constant":
		# constant
		c.duration.quarterLength = note_len
		notes.append(copy.deepcopy(note1))
		first_note = note1.name

		# first axis
		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# second axis
		note1.transpose(j,inPlace=True)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# third axis
		note1.transpose(k,inPlace=True)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		current_note = note1.name
		condition = (current_note!=first_note)

		# begin repetition
		while condition:
			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave, oct)
			notes.append(copy.deepcopy(note1))

			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave, oct)
			notes.append(copy.deepcopy(note1))

			note1.transpose(k,inPlace=True)
			f_octave(note1,ottave, oct)
			notes.append(copy.deepcopy(note1))
			current_note = note1.name
			condition = (current_note!=first_note)

	else:
		# free
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		first_note = note1.name

		# first axis
		note1.transpose(i,inPlace=True)
		f_durata(note1)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# second axis
		note1.transpose(j,inPlace=True)
		f_durata(note1)
		f_octave(note1,ottave, oct)
		notes.append(copy.deepcopy(note1))

		# third axis
		note1.transpose(k,inPlace=True)
		f_octave(note1,ottave, oct)
		f_durata(note1)
		notes.append(copy.deepcopy(note1))

		current_note = note1.name
		condition = (current_note!=first_note)

		# begin repetition
		while condition:
			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave, oct)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))

			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave, oct)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))

			note1.transpose(k,inPlace=True)
			f_octave(note1,ottave, oct)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))
			current_note = note1.name
			condition = (current_note!=first_note)

	melody = stream.Stream()

	# end of procedure
	if bass_clef:
		melody.insert(0, clef.BassClef())
		melody.append(notes)
		melody_bass = melody.transpose(-24)
		melody = melody_bass
	else:
		melody.append(notes)
   
	return(melody)
