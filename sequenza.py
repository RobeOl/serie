import random
from music21 import *
from binary import genera_binary
from quaternary import genera_quaternary

def genera_sequenza(seq_type,tipo,note_len,i,j,i1,j1,i2,j2,ottave,bass_clef,starting_note,harmony,harmony_type):

    if seq_type=="Binary":
        s = genera_binary(tipo,note_len,i,j,ottave,bass_clef,starting_note,harmony,harmony_type)
    else:
        s = genera_quaternary(tipo,note_len,i1,j1,i2,j2,ottave,bass_clef,starting_note,harmony,harmony_type)

    return(s)