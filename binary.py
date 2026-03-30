from music21 import *
import random
import copy

def f_octave(x,ottave):
	if ottave == 1:
	    # limit notes to octaves 4-5
	    if x.octave==6:
 	       x.octave=4

def f_durata(x):
    x.duration.quarterLength = random.choice([1, 1/2, 1/4])

def genera_binary(tipo,note_len,i,j,starting_note,ottave=1):
	#lista_note = ["C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4","A#4","B4"]
	#nota_in= lista_note[starting_note]
	#c = note.Note(nota_in)
	c = note.Note(starting_note)
	#c = note.Note("C#")

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
