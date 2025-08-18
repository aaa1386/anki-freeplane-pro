import uuid
import os
import urllib.parse

class Node:
    def __init__(self, doc, element, file_path=None):
        self.doc = doc
        self.element = element
        self.file_path = file_path
        self.fields = False
        self.children = False
        self._cached_node_id = None

    # ------------------ شناسه نود ------------------
    def get_node_id(self):
        if self._cached_node_id is not None:
            return self._cached_node_id
        node_id = self.element.get('ID') or str(uuid.uuid4())
        if node_id.startswith('ID_'):
            node_id = node_id[3:]
        self._cached_node_id = node_id
        return node_id

    # ------------------ بررسی کارت ------------------
    def should_create_card(self):
        model_attr = self.element.find('attribute[@NAME="anki:model"]')
        deck_attr = self.element.find('attribute[@NAME="anki:deck"]')
        return bool(model_attr or deck_attr)

    # ------------------ مدل کارت ------------------
    def get_model(self):
        model = self.element.find('attribute[@NAME="anki:model"]')
        if model is not None and model.get('VALUE'):
            return model.get('VALUE')
        return 'Freeplane basic'

    # ------------------ دسته کارت ------------------
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

    # ------------------ فیلدهای کارت ------------------
    def get_fields(self):
        if self.fields is not False:
            return self.fields

        fields = {}
        attributes = self.element.findall('attribute')
        node_text = self.element.get('TEXT') or ''
        node_id = self.get_node_id()

        for attr in attributes:
            name = attr.get('NAME')
            if name and name.startswith('anki:field:'):
                field_name = name[len('anki:field:'):]
                value = attr.get('VALUE') or ''
                if value == '*':
                    value = node_text
                fields[field_name] = value

        fields['Front'] = node_text
        fields['Path'] = self.__build_custom_path_link(node_id)

        self.fields = fields
        return fields

    # ------------------ پشت کارت ------------------
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

    # ------------------ لینک مسیر ------------------
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

        # حذف خود کارت از مسیر (مثل نسخه قبلی)
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

    # ------------------ فرزندان ------------------
    def get_children(self):
        if self.children is False:
            children_nodes = []
            for child_element in self.element.findall('node'):
                child_node = Node(self.doc, child_element, self.file_path)
                children_nodes.append(child_node)
            self.children = children_nodes
        return self.children

    # ------------------ نودهای کارت‌دار ------------------
    def get_card_nodes(self):
        card_nodes = []
        if self.should_create_card():
            card_nodes.append(self)
        for child in self.get_children():
            card_nodes.extend(child.get_card_nodes())
        return card_nodes

    # ------------------ کمکی‌ها ------------------
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
        fields['Back'] = self.get_back_content()
        return {
            'id': self.get_node_id(),
            'deck': self.get_final_deck(),
            'model': self.get_model(),
            'fields': fields,
            'PFile': self.file_path or ''
        }
