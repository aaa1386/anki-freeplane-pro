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

    # ------------------ تبدیل به دیکشنری ------------------
    def to_dict(self):
        return {
            'id': self.get_node_id(),
            'deck': self.get_final_deck(),
            'model': self.get_model(),
            'fields': self.get_fields()  # توجه: Path فقط نگهداری داخلی
        }

    # ------------------ گرفتن فیلدها ------------------
    def get_fields(self, fields=None):
        if fields is None:
            fields = {}

        if self.fields is False:
            fields = self.__parse_fields(fields)
            # Front و Back مثل سابق
            if 'Back' not in fields or not fields['Back']:
                outline = self.__build_outline_recursive(self.get_children(), depth=0)
                fields['Back'] = outline
            # نگهداری Path برای استفاده داخلی، ولی به آنکی تزریق اجباری نمی‌کنیم
            fields['_Path'] = fields.get('Path', '')
            # Path اصلی حذف می‌شود از این مرحله تا اجباری تزریق نشود
            if 'Path' in fields:
                del fields['Path']

            self.fields = {k: (v or '') for k, v in fields.items()}

        return self.fields

    def __parse_fields(self, fields):
        attributes = self.element.findall('attribute')
        node_text = self.element.get('TEXT') or ''
        node_id = self.get_node_id()

        # Front فقط متن ساده نود
        fields['Front'] = node_text

        # گرفتن سایر فیلدهای آنکی
        for attr in attributes:
            name = attr.get('NAME')
            if name and name.startswith('anki:field:'):
                field_name = name[len('anki:field:'):]
                value = attr.get('VALUE') or ''
                if value == '*':
                    value = node_text
                fields[field_name] = value

        # Path شامل لینک راست‌چین مسیر سلسله مراتبی، اما فعلاً نگهداری داخلی
        fields['Path'] = self.__build_custom_path_link(node_id)

        return fields

    # ------------------ سایر متدها همانند قبل ------------------
    def get_node_id(self):
        if self._cached_node_id is not None:
            return self._cached_node_id
        node_id = self.element.get('ID')
        if not node_id:
            node_id = str(uuid.uuid4())
        if node_id.startswith('ID_'):
            node_id = node_id[3:]
        self._cached_node_id = node_id
        return node_id

    def get_model(self):
        return self.get_attribute('anki:model') or 'Freeplane basic'

    def get_deck(self):
        deck_attr = self.element.find('attribute[@NAME="anki:deck"]')
        if deck_attr is not None and deck_attr.get('VALUE') and deck_attr.get('VALUE').strip():
            return deck_attr.get('VALUE').strip()
        current = self.element
        while True:
            parent = self.__get_parent_node(current)
            if parent is None:
                return 'FreeplaneDeck'
            deck_attr = parent.find('attribute[@NAME="anki:deck"]')
            if deck_attr is not None and deck_attr.get('VALUE') and deck_attr.get('VALUE').strip():
                return deck_attr.get('VALUE').strip()
            current = parent

    def get_final_deck(self):
        deck = self.get_deck()
        return deck if deck else 'FreeplaneDeck'

    def __get_parent_node(self, element):
        current_id = element.get('ID')
        for node in self.doc.findall('.//node'):
            for child in node.findall('node'):
                if child.get('ID') == current_id:
                    return node
        return None

    def should_create_card(self):
        model_attr = self.element.find('attribute[@NAME="anki:model"]')
        deck_attr = self.element.find('attribute[@NAME="anki:deck"]')
        return bool(model_attr or deck_attr)

    def get_children(self):
        if self.children is False:
            self.children = [Node(self.doc, c, self.file_path) for c in self.element.findall('node')]
        return self.children

    def get_text(self):
        return self.element.get('TEXT') or ''

    # ------------------ سایر متدهای HTML و اوت‌لاین همانند قبل ------------------
    # (__build_custom_path_link و __build_outline_recursive و get_attribute)
