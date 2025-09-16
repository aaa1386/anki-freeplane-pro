# Based on lajohnston/anki-freeplane (MIT), developed by aaa1386
import os
import xml.etree.ElementTree as ET
from .node import Node

class Reader:
    def get_notes(self, doc, file_path=None):
        all_nodes = doc.findall('.//node')
        notes = []

        for element in all_nodes:
            node = Node(doc, element, file_path=file_path)
            if node.should_create_card():
<<<<<<< HEAD
                note_dict = node.to_dict()
                # تغییر فیلد Path به Ancestors
                if "fields" in note_dict and "Path" in note_dict["fields"]:
                    note_dict["fields"]["Ancestors"] = note_dict["fields"].pop("Path")
                notes.append(note_dict)
=======
                notes.append(node.to_dict())
>>>>>>> 3d1e6b30ee7ccd873e864d22b70788c5ca7f2045

        print(f"Found {len(notes)} notes in mindmap")
        return notes

def read_all_mm(folder_path):
    all_notes = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.mm'):
                file_path = os.path.join(root, file)
                doc = ET.parse(file_path)
                root_element = doc.getroot().find('node')
                if root_element is None:
                    continue
                reader = Reader()
                notes = reader.get_notes(doc, file_path=file_path)
                all_notes.extend(notes)
    return all_notes

if __name__ == "__main__":
    folder_path = r"D:\FreeplaneMaps"
    all_notes = read_all_mm(folder_path)
    for note in all_notes:
        print(note['fields']['Front'], note['model'], note['deck'])
