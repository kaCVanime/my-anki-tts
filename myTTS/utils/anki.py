from .anki_connect import invoke as anki_invoke


def find_notes(query):
    return anki_invoke("findNotes", query=query)

def get_note_info(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note(nid):
    note = get_note_info(nid)
    fields = {key: value_dict["value"] for key, value_dict in note["fields"].items()}
    return {
        "fields": fields,
        "tags": note["tags"]
    }
