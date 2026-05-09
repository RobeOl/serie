import random
from music21 import *
from binary import genera_binary
from quaternary import genera_quaternary
from senary import genera_senary
from ternary import genera_ternary

def genera_sequenza(seq_type,tipo,note_len,i,j,i1,j1,i2,j2,ii1,jj1,ii2,jj2,ii3,jj3,int_i,int_j,int_k,ottave,bass_clef,starting_note,harmony,harmony_type):

    if seq_type=="Binary":
        s = genera_binary(tipo,note_len,i,j,ottave,bass_clef,starting_note,harmony,harmony_type)
    elif seq_type=="Quaternary":
        s = genera_quaternary(tipo,note_len,i1,j1,i2,j2,ottave,bass_clef,starting_note,harmony,harmony_type)
    elif seq_type=="Senary":
        s = genera_senary(tipo,note_len,ii1,jj1,ii2,jj2,ii3,jj3,ottave,bass_clef,starting_note,harmony,harmony_type)
    else:
        s = genera_ternary(tipo,note_len,int_i,int_j,int_k,ottave,bass_clef,starting_note,harmony,harmony_type)
    return(s)