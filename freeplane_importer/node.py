# Based on lajohnston/anki-freeplane (MIT), developed by aaa1386
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


    def to_dict(self):
        return {
            'id': self.get_node_id(),
            'deck': self.get_final_deck(),
            'model': self.get_model(),
            'fields': self.get_fields()
        }


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


    def get_final_deck(self):
        deckbranch = self.get_attribute('anki:deckbranch')
        if deckbranch is not None:
            deckbranch = deckbranch.strip()
            if deckbranch:
                return deckbranch

        deck = self.get_attribute('anki:deck')
        if deck and deck.strip():
            return deck.strip()

        current = self.element
        while True:
            parent = self.__get_parent_node(current)
            if parent is None:
                return 'FreeplaneDeck'
            parent_deckbranch = parent.find('attribute[@NAME="anki:deckbranch"]')
            if parent_deckbranch is not None:
                val = parent_deckbranch.get('VALUE')
                if val and val.strip():
                    return val.strip()
            current = parent


    def __get_parent_node(self, element):
        current_id = element.get('ID')
        for node in self.doc.findall('.//node'):
            for child in node.findall('node'):
                if child.get('ID') == current_id:
                    return node
        return None


    def should_create_card(self):
        return any(
            self.element.find(f'attribute[@NAME="{name}"]') is not None
            for name in ['anki:model', 'anki:deck', 'anki:deckbranch']
        )


    def get_fields(self, fields=None):
        if fields is None:
            fields = {}
        if self.fields is False:
            fields = self.__parse_fields(fields)
            if 'Back' not in fields or not fields['Back']:
                max_layers = self.get_max_layers()
                outline = self.__build_outline_recursive(self.get_children(), depth=0, max_depth=max_layers)
                fields['Back'] = outline
            self.fields = {k: (v or '') for k, v in fields.items()}
        return self.fields


    def __parse_fields(self, fields):
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
        return fields


    def __build_custom_path_link(self, node_id):
        if not self.file_path:
            return ''
        abs_path = os.path.abspath(self.file_path).replace("\\\\", "/")
        encoded_path = urllib.parse.quote(abs_path)
        anchor = 'ID_' + node_id
        path_nodes = []
        current = self.element
        while current is not None:
            path_nodes.append(current.get('TEXT') or '')
            current = self.__get_parent_node(current)
        path_nodes.reverse()
        min_nodes = 5
        max_total_words = 30
        def count_words(seq):
            return sum(len(s.split()) for s in seq)
        if len(path_nodes) <= min_nodes and count_words(path_nodes) <= max_total_words:
            nodes_to_display = path_nodes
        else:
            root = path_nodes[0]
            tail_nodes = path_nodes[1:]
            count_tail = max(min_nodes - 1, len(tail_nodes))
            tail_nodes = tail_nodes[-count_tail:]
            result_nodes = [root]
            total_words = len(root.split())
            for node_text in tail_nodes:
                remaining_words = max_total_words - total_words
                if remaining_words <= 0:
                    break
                words = node_text.split()
                if len(words) > remaining_words:
                    node_text = " ".join(words[:remaining_words]) + "..."
                total_words += len(node_text.split())
                result_nodes.append(node_text)
            if len(path_nodes) > min_nodes + len(tail_nodes):
                result_nodes.insert(1, "...")
            nodes_to_display = result_nodes
        rtl_nodes = [f'<span dir="rtl" style="direction: rtl; unicode-bidi: embed;">{node}</span>' if node != "..." else "..." for node in nodes_to_display]
        if len(rtl_nodes) > 1:
            path_text = " ← ".join(rtl_nodes[:-1]) + " ←"
        else:
            path_text = "←"
        full_path_link = f'<a href="freeplane:/%20/{encoded_path}#{anchor}" style="text-decoration:none; color:#007acc;">{path_text}</a>'
        return full_path_link


    def __build_outline_recursive(self, children, depth=0, max_depth=3):
        if not children or depth >= max_depth:
            return ''
        bullet_styles = ['square', 'disc', 'circle']
        bullet = bullet_styles[depth % len(bullet_styles)]
        html = f'<ul style="list-style-type: {bullet}; margin: 0 0 0 1.5em; padding-left: 0; direction: rtl; text-align: right;">'
        for child in children:
            if child.should_create_card() and depth > 0:
                continue
            text = child.get_text() or ''
            sub_outline = child.__build_outline_recursive(child.get_children(), depth + 1, max_depth)
            html += f'<li>{text}'
            if sub_outline:
                html += sub_outline
            html += '</li>'
        html += '</ul>'
        return html


    def get_attribute(self, name):
        attr = self.element.find(f'attribute[@NAME="{name}"]')
        if attr is not None:
            return attr.get('VALUE') or ''
        return ''


    def get_max_layers(self):
        val = self.get_attribute('BackLevels')  # نام attribute جدید
        try:
            layers = int(val)
            if layers >= 0:
                return layers
        except (ValueError, TypeError):
            pass
        return 3  # مقدار پیش‌فرض

    def get_children(self):
        if self.children is False:
            self.children = [Node(self.doc, e, self.file_path) for e in self.element.findall('node')]
        return self.children


    def get_text(self):
        return self.element.get('TEXT') or ''
