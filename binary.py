from music21 import *
import random
import copy

def f_octave(x, ottave):
    if (ottave == 1) and (x.octave == 5):
        # limit notes to octaves 4-5
        x.octave = 4
    elif (ottave == 1) and (x.octave > 5):
        x.octave = 4
    elif (ottave == 2) and (x.octave > 5):
        x.octave = 4


def f_durata(x):
    x.duration.quarterLength = random.choice([1, 1/2, 1/4])

def genera_binary(tipo,note_len,i,j,ottave,starting_note):
	c = note.Note(starting_note)

	if starting_note <= 7:
		c.octave = 4
	else:
		c.octave = 3

	notes = []

	# first interval, starting with C4
	note1 = c

	if tipo=="sequence-constrained":
		# sequence-constrained
	
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		prima = note1.name

		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave)
		notes.append(copy.deepcopy(note1))
		seconda = note1.name
		first_couple = [prima,seconda]
	
		#print('FIRST: ',first_couple)


		condition = True
		# following leaps/intervals
		while condition: 
			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))
			prima = note1.name

			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave)
			notes.append(copy.deepcopy(note1))
			seconda = note1.name
		
			current_couple = [prima,seconda]
			condition = (current_couple!=first_couple)
			#print(current_couple)
	
	elif tipo=="length-constrained":
		# length-constrained
		conta = 1
		note_number = random.choice([2,3,5,6])

		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		prima = note1.name

		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave)
		if conta==note_number:
			f_durata(note1)
			conta=1
		else:
			conta = conta+1

		notes.append(copy.deepcopy(note1))
		seconda = note1.name
		first_couple = [prima,seconda]
	
		#print('FIRST: ',first_couple)


		condition = True
		# following leaps/intervals
		while condition: 
			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave)
			if conta==note_number:
				f_durata(note1)
				conta=1
			else:
				conta = conta+1
			notes.append(copy.deepcopy(note1))
			prima = note1.name

			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave)
			if conta==note_number:
				f_durata(note1)
				conta=1
			else:
				conta = conta+1
			notes.append(copy.deepcopy(note1))
			seconda = note1.name
		
			current_couple = [prima,seconda]
			condition = (current_couple!=first_couple)
			#print(current_couple)

	elif tipo=="constant":
		# constant
		c.duration.quarterLength = note_len
		notes.append(copy.deepcopy(note1))
		prima = note1.name

		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave)
		notes.append(copy.deepcopy(note1))
		seconda = note1.name
		first_couple = [prima,seconda]
	
		#print('FIRST: ',first_couple)


		condition = True
		# following leaps/intervals
		while condition: 
			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave)
			notes.append(copy.deepcopy(note1))
			prima = note1.name

			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave)
			notes.append(copy.deepcopy(note1))
			seconda = note1.name
		
			current_couple = [prima,seconda]
			condition = (current_couple!=first_couple)
			#print(current_couple)

	else:
		# free
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		prima = note1.name

		note1.transpose(i,inPlace=True)
		f_octave(note1,ottave)
		f_durata(note1)
		notes.append(copy.deepcopy(note1))
		seconda = note1.name
		first_couple = [prima,seconda]
	
		#print('FIRST: ',first_couple)


		condition = True
		# following leaps/intervals
		while condition: 
			note1.transpose(j,inPlace=True)
			f_octave(note1,ottave)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))
			prima = note1.name

			note1.transpose(i,inPlace=True)
			f_octave(note1,ottave)
			f_durata(note1)
			notes.append(copy.deepcopy(note1))
			seconda = note1.name
		
			current_couple = [prima,seconda]
			condition = (current_couple!=first_couple)
			#print(current_couple)

	melody = stream.Stream()

	# remove last element
	notes.pop()
	melody.append(notes)

	return(melody)
