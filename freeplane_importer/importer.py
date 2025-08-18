from .model_not_found_exception import ModelNotFoundException
import os


class Importer:
    def __init__(self, collection):
        self.collection = collection
        self.model = False
        self.model_fields = []

    def import_note(self, import_data):
        try:
            self.__load_model(import_data['model'])

            did = self.collection.decks.id(import_data['deck'], create=True)
            self.collection.decks.select(did)

            note = self.__find_or_create_note(import_data['id'], import_data['PFile'])
            self.__populate_note_fields(note, import_data['fields'], import_data['id'], import_data['PFile'])

            is_new = note.id == 0
            if is_new:
                note.model()['did'] = did
                self.collection.addNote(note)
            else:
                for card in note.cards():
                    if card.did != did:
                        card.did = did
                        card.flush()

            note.flush()
            return True

        except Exception as e:
            print(f"Error importing note ID {import_data.get('id')} - PFile {import_data.get('PFile')}: {e}")
            return False

    def __load_model(self, model_name):
        model = self.collection.models.byName(model_name)
        if model is None:
            raise ModelNotFoundException(model_name)

        self.collection.models.setCurrent(model)
        self.model = model
        self.model_fields = self.collection.models.fieldNames(self.model)

    def __populate_note_fields(self, note, fields, node_id, pfile):
        id_field = self.__get_model_id_field()
        if id_field is not None:
            note[id_field] = node_id or ''

        pfile_field = self.__get_model_pfile_field()
        if pfile_field is not None:
            note[pfile_field] = pfile or ''

        for field in self.model_fields:
            if field != id_field and field != pfile_field:
                note[field] = fields.get(field, '') or ''

    def __get_model_id_field(self):
        if len(self.model_fields) > 0 and self.model_fields[0].lower() == 'id':
            return self.model_fields[0]
        return None

    def __get_model_pfile_field(self):
        for f in self.model_fields:
            if f.lower() == 'pfile':
                return f
        return None

    def __find_or_create_note(self, node_id, pfile):
        import os

        id_field = self.__get_model_id_field()
        pfile_field = self.__get_model_pfile_field()

        # نرمال‌سازی مسیر PFile برای تطابق دقیق‌تر
        pfile_norm = os.path.normcase(os.path.normpath(pfile)).strip() if pfile else ''

        note_ids = self.collection.findNotes(f"mid:{self.model['id']}")

        for nid in note_ids:
            note = self.collection.getNote(nid)
            if note is None:
                continue

            note_id_value = note[id_field].strip() if id_field and id_field in note else ''
            note_pfile_value = (
                os.path.normcase(os.path.normpath(note[pfile_field])).strip()
                if pfile_field and pfile_field in note else ''
            )

            if note_id_value == node_id and note_pfile_value == pfile_norm:
                return note

        return self.collection.newNote()
