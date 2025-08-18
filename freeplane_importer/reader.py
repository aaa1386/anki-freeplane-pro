import os
import uuid
import urllib.parse
import xml.etree.ElementTree as ET


class Node:
    def __init__(self, doc, element, file_path=None):
        self.doc = doc
        self.element = element
        self.file_path = file_path
        self.fields = False
        self.children = False
        self._cached_node_id = None

    def get_node_id(self):
        if self._cached_node_id is not None:
            return self._cached_node_id
        node_id = self.element.get('ID') or str(uuid.uuid4())
        if node_id.startswith('ID_'):
            node_id = node_id[3:]
        self._cached_node_id = node_id
        return node_id

    def should_create_card(self):
        model_attr = self.element.find('attribute[@NAME="anki:model"]')
        deck_attr = self.element.find('attribute[@NAME="anki:deck"]')
        return bool(model_attr or deck_attr)

    def get_model(self):
        model = self.element.find('attribute[@NAME="anki:model"]')
        if model is not None and model.get('VALUE'):
            return model.get('VALUE')
        return 'Freeplane basic'

    def get_deck(self):
        deck_attr = self.element.find('attribute[@NAME="anki:deck"]')
        if deck_attr is not None and deck_attr.get('VALUE') and deck_attr.get('VALUE').strip():
            return deck_attr.get('VALUE').strip()
        return None

    def get_final_deck(self):
        deck = self.get_deck()
        if deck:
            return deck

        current = self.element
        while True:
            parent = self.__get_parent_node(current)
            if parent is None:
                return 'FreeplaneDeck'

            parent_model = parent.find('attribute[@NAME="anki:model"]')
            parent_deck = parent.find('attribute[@NAME="anki:deck"]')

            if parent_model is not None:
                if parent_deck is not None and parent_deck.get('VALUE') and parent_deck.get('VALUE').strip():
                    return parent_deck.get('VALUE').strip()
                else:
                    return 'FreeplaneDeck'

            current = parent

    def get_fields(self):
        if self.fields is not False:
            return self.fields

        fields = {}
        attributes = self.element.findall('attribute')
        node_text = self.element.get('TEXT') or ''
        node_id = self.get_node_id()

        has_field_attr = False
        for attr in attributes:
            name = attr.get('NAME')
            if name and name.startswith('anki:field:'):
                has_field_attr = True
                field_name = name[len('anki:field:'):]
                value = attr.get('VALUE') or ''
                if value == '*':
                    value = node_text
                fields[field_name] = value

        fields['Front'] = node_text
        fields['Path'] = self.__build_custom_path_link(node_id)

        self.fields = fields
        return fields

    def get_back_content(self):
        fields = self.get_fields()
        back_value = fields.get('Back', '').strip()
        if back_value:
            return back_value
        return self._build_back_from_children()

    def _build_back_from_children(self):
        children = self.get_children()
        if not children:
            return ''

        symbols = ['■', '●', '○']
        max_symbols = len(symbols)

        def recurse(nodes, level=0):
            lines = []
            symbol = symbols[min(level, max_symbols - 1)]
            for node in nodes:
                text = node.get_text().strip()
                if not text:
                    continue
                lines.append(f"{symbol} {text}")
                child_lines = recurse(node.get_children(), level + 1)
                if child_lines:
                    indented = ['  ' + l for l in child_lines]
                    lines.extend(indented)
            return lines

        lines = recurse(children)
        return '\n'.join(lines)

    def __build_custom_path_link(self, node_id):
        if not self.file_path:
            return ''
        abs_path = os.path.abspath(self.file_path).replace("\\", "/")
        encoded_path = urllib.parse.quote(abs_path)
        anchor = 'ID_' + node_id

        path_nodes = []
        current = self.element
        while current is not None:
            path_nodes.append(current.get('TEXT') or '')
            current = self.__get_parent_node(current)
        path_nodes.reverse()

        # حذف خود کارت از مسیر
        if len(path_nodes) > 1:
            path_nodes = path_nodes[:-1]

        min_nodes = 5
        max_total_words = 30

        def count_words(seq):
            return sum(len(s.split()) for s in seq)

        if len(path_nodes) <= min_nodes and count_words(path_nodes) <= max_total_words:
            path_text = " ← ".join(path_nodes)
        else:
            path_text = " ← ".join([path_nodes[0]] + ["..."] + path_nodes[-(min_nodes - 1):])

        return f'<a href="freeplane:/%20/{encoded_path}#{anchor}" style="text-decoration:none;">{path_text}</a>'

    def get_children(self):
        if self.children is False:
            children_nodes = []
            for child_element in self.element.findall('node'):
                child_node = Node(self.doc, child_element, self.file_path)
                children_nodes.append(child_node)
            self.children = children_nodes
        return self.children

    def get_card_nodes(self):
        card_nodes = []
        if self.should_create_card():
            card_nodes.append(self)
        for child in self.get_children():
            card_nodes.extend(child.get_card_nodes())
        return card_nodes

    def __get_parent_node(self, element):
        current_id = element.get('ID')
        for node in self.doc.findall('.//node'):
            for child in node.findall('node'):
                if child.get('ID') == current_id:
                    return node
        return None

    def get_text(self):
        return self.element.get('TEXT') or ''

    def to_dict(self):
        fields = self.get_fields()
        fields['Back'] = self.get_back_content()  # مقدار Back جایگزین می‌شود
        return {
            'id': self.get_node_id(),
            'deck': self.get_final_deck(),
            'model': self.get_model(),
            'fields': fields,
            'PFile': self.file_path or ''
        }


class Reader:
    def get_notes(self, doc, file_path=None):
        all_nodes = doc.findall('.//node')
        notes = []

        for element in all_nodes:
            model_attr = element.find('attribute[@NAME="anki:model"]')
            deck_attr = element.find('attribute[@NAME="anki:deck"]')

            if model_attr is None and deck_attr is None:
                continue

            node = Node(doc, element, file_path=file_path)
            notes.append(node.to_dict())

        print(f"Found {len(notes)} notes in mindmap")  # پیام انگلیسی
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
    folder_path = r"D:\FreeplaneMaps"  # مسیر پوشه فایل‌های mm
    all_notes = read_all_mm(folder_path)
    for note in all_notes:
        print(note['fields']['Front'], note['model'], note['deck'])
