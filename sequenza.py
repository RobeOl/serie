from multidimensional import genera_multidimensional


def genera_sequenza(tipo, note_len, K, starting_note, repeated=True):
    """
    Wrapper chiamato da app.py per la route /multidimensional.

    Parametri
    ---------
    tipo          : str   – modalità ritmica
    note_len      : float – durata nota per modalità "constant"
    K             : int   – numero di note (2–12)
    starting_note : int   – pitch-class 0-11
    repeated      : bool  – note ripetibili o no
    """
    return genera_multidimensional(tipo, note_len, K, starting_note, repeated)
