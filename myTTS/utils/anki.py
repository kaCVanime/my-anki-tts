from .anki_connect import invoke as anki_invoke


def find_notes(query):
    return get_notes_info(anki_invoke("findNotes", query=query))

def get_notes_info(nids):
    return [get_note_detail(note) for note in anki_invoke("notesInfo", notes=nids)]

def get_note_detail(note):
    fields = {key: value_dict["value"] for key, value_dict in note["fields"].items()}
    return {
        "fields": fields,
        "tags": note["tags"]
    }
