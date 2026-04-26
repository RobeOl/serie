import random
from music21 import *
from binary import genera_binary
from quaternary import genera_quaternary
import copy

def genera_sequenza(seq_type,tipo,note_len,i,j,ii,jj,ottave,bass_clef,starting_note,harmony,harmony_type):

    if seq_type=="Binary":
        s = genera_binary(tipo,note_len,i,j,ottave,bass_clef,starting_note,harmony,harmony_type)
    else
        s = genera_quaternary(tipo,note_len,i,j,ii,jj,ottave,bass_clef,starting_note,harmony,harmony_type)

    return(s)