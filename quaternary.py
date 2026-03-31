import random
from music21 import *
import copy

def f_octave(x, ottave, oct):
    if (ottave == 1) and (x.octave >= 6):
        if x.octave==(oct+3):
        	x.octave=oct
    elif (ottave == 2) and (x.octave > 6):
        x.octave = oct

def f_durata(x):
	# x.duration.quarterLength = random.choice([1, 1/2, 1/4])
	x.duration.quarterLength = random.choice([1, 1/2, 1/4])

def genera_quaternary(tipo,note_len,i,j,ii,jj,ottave,starting_note=0):
    x = note.Note(starting_note)

    if starting_note <= 6:
	    x.octave = 4
    else:
	    x.octave = 3

    oct = x.octave

    notes = []

    # first interval, starting with C4
    note1 = x

    if tipo=="sequence-constrained":
        # sequence-constrained

        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name
        first_couple = [prima,seconda]

        # print('FIRST: ',first_couple)

        # first jump
        note1.transpose(j,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # second interval
        note1.transpose(ii,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        # second jump
        note1.transpose(jj,inPlace=True)
        f_octave(note1,ottave, oct)
        # change time
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # begin repetition
        # first interval
        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        condition = True
        # following intervals
        while condition:
            note1.transpose(j,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(ii,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
                
            note1.transpose(jj,inPlace=True)
            f_octave(note1,ottave, oct)
            # change time
            f_durata(note1)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(i,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
            current_couple = [prima,seconda]
            condition = (current_couple!=first_couple)
            # print('CURRENT: ',current_couple)

    elif tipo=="length-constrained":
        # length-constrained
        conta = 1
        note_number = random.choice([2,3,5,6])

        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        note1.transpose(i,inPlace=True)
        conta = conta+1
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name
        first_couple = [prima,seconda]

        # print('FIRST: ',first_couple)

        # first jump
        note1.transpose(j,inPlace=True)
        f_octave(note1,ottave, oct)
        if conta==note_number:
            f_durata(note1)
            conta=1
        else:
            conta = conta+1

        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # second interval
        note1.transpose(ii,inPlace=True)
        f_octave(note1,ottave, oct)
        if conta==note_number:
            f_durata(note1)
            conta=1
        else:
            conta = conta+1

        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        # second jump
        note1.transpose(jj,inPlace=True)
        f_octave(note1,ottave, oct)
        if conta==note_number:
            f_durata(note1)
            conta=1
        else:
            conta = conta+1

        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # begin repetition
        # first interval
        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        if conta==note_number:
            f_durata(note1)
            conta=1
        else:
            conta = conta+1

        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        condition = True
        # following intervals
        while condition:
            note1.transpose(j,inPlace=True)
            f_octave(note1,ottave, oct)
            if conta==note_number:
                f_durata(note1)
                conta=1
            else:
                conta = conta+1
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(ii,inPlace=True)
            f_octave(note1,ottave, oct)
            if conta==note_number:
                f_durata(note1)
                conta=1
            else:
                conta = conta+1

            notes.append(copy.deepcopy(note1))
            seconda = note1.name
                
            note1.transpose(jj,inPlace=True)
            f_octave(note1,ottave, oct)
            if conta==note_number:
                f_durata(note1)
                conta=1
            else:
                conta = conta+1

            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(i,inPlace=True)
            f_octave(note1,ottave, oct)
            if conta==note_number:
                f_durata(note1)
                conta=1
            else:
                conta = conta+1
                
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
            current_couple = [prima,seconda]
            condition = (current_couple!=first_couple)
            # print('CURRENT: ',current_couple)

    elif tipo=="constant":
        # constant 
        x.duration.quarterLength = note_len
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name
        first_couple = [prima,seconda]

        # print('FIRST: ',first_couple)

        # first jump
        note1.transpose(j,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # second interval
        note1.transpose(ii,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        # second jump
        note1.transpose(jj,inPlace=True)
        f_octave(note1,ottave, oct)
        # change time
        #f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # begin repetition
        # first interval
        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        condition = True
        # following intervals
        while condition:
            note1.transpose(j,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(ii,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
                
            note1.transpose(jj,inPlace=True)
            f_octave(note1,ottave, oct)
            # change time
            #f_durata(note1)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(i,inPlace=True)
            f_octave(note1,ottave, oct)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
            current_couple = [prima,seconda]
            condition = (current_couple!=first_couple)
            #print('CURRENT: ',current_couple)

    else:
        # free 
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name
        first_couple = [prima,seconda]

        # print('FIRST: ',first_couple)

        # first jump
        note1.transpose(j,inPlace=True)
        f_octave(note1,ottave, oct)
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # second interval
        note1.transpose(ii,inPlace=True)
        f_octave(note1,ottave, oct)
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        # second jump
        note1.transpose(jj,inPlace=True)
        f_octave(note1,ottave, oct)
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # begin repetition
        # first interval
        note1.transpose(i,inPlace=True)
        f_octave(note1,ottave, oct)
        f_durata(note1)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        condition = True
        # following intervals
        while condition:
            note1.transpose(j,inPlace=True)
            f_octave(note1,ottave, oct)
            f_durata(note1)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(ii,inPlace=True)
            f_octave(note1,ottave, oct)
            f_durata(note1)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
                
            note1.transpose(jj,inPlace=True)
            f_octave(note1,ottave, oct)
            f_durata(note1)
            notes.append(copy.deepcopy(note1))
            prima = note1.name

            note1.transpose(i,inPlace=True)
            f_octave(note1,ottave, oct)
            f_durata(note1)
            notes.append(copy.deepcopy(note1))
            seconda = note1.name
            current_couple = [prima,seconda]
            condition = (current_couple!=first_couple)
            #print('CURRENT: ',current_couple)

    
        
    melody = stream.Stream()

    # remove last element
    notes.pop()
    melody.append(notes)

    

    return(melody)

