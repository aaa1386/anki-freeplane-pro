# Based on lajohnston/anki-freeplane (MIT), developed by aaa1386
import os
import xml.etree.ElementTree as ET
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import QAction, QFileDialog, QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox
from .freeplane_importer.model_not_found_exception import ModelNotFoundException
from .freeplane_importer.reader import Reader
from .freeplane_importer.importer import Importer
from .freeplane_importer.node import Node

# ============================
# Exclude files for different operations
# ============================
EXCLUDE_FROM_DELETE_FILE = os.path.join(os.path.dirname(__file__), "exclude_delete.txt")
EXCLUDE_FROM_SYNC_FILE = os.path.join(os.path.dirname(__file__), "exclude_sync.txt")

# ============================
# Manage excluded paths
# ============================
def load_exclude_list(exclude_file):
    if os.path.exists(exclude_file):
        with open(exclude_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_exclude_list(lst, exclude_file):
    with open(exclude_file, "w", encoding="utf-8") as f:
        for item in lst:
            f.write(f"{item}\n")

class ExcludeManagerDialog(QDialog):
    def __init__(self, exclude_file, title, parent=None):
        super().__init__(parent)
        self.exclude_file = exclude_file
        self.setWindowTitle(title)
        self.resize(600, 400)

        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self.load_list()

        self.btn_add_file = QPushButton("Add File")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_remove = QPushButton("Remove Selected")
        self.layout.addWidget(self.btn_add_file)
        self.layout.addWidget(self.btn_add_folder)
        self.layout.addWidget(self.btn_remove)

        self.btn_add_file.clicked.connect(self.add_file)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove.clicked.connect(self.remove_selected)

    def load_list(self):
        self.list_widget.clear()
        for path in load_exclude_list(self.exclude_file):
            self.list_widget.addItem(path)

    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(caption="Select a file to exclude")
        if file_path:
            lst = load_exclude_list(self.exclude_file)
            if file_path not in lst:
                lst.append(file_path)
                save_exclude_list(lst, self.exclude_file)
                self.load_list()
                QMessageBox.information(self, "Success", f"File {file_path} added to exclude list.")

    def add_folder(self):
        folder_path = QFileDialog.getExistingDirectory(caption="Select a folder to exclude")
        if folder_path:
            lst = load_exclude_list(self.exclude_file)
            if folder_path not in lst:
                lst.append(folder_path)
                save_exclude_list(lst, self.exclude_file)
                self.load_list()
                QMessageBox.information(self, "Success", f"Folder {folder_path} added to exclude list.")

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        lst = load_exclude_list(self.exclude_file)
        for item in selected_items:
            path = item.text()
            if path in lst:
                lst.remove(path)
        save_exclude_list(lst, self.exclude_file)
        self.load_list()
        QMessageBox.information(self, "Success", "Selected path(s) removed.")

def open_exclude_manager(exclude_file, title):
    dlg = ExcludeManagerDialog(exclude_file, title, mw)
    dlg.exec()

# ============================
# QAction menu items
# ============================
action_manage_delete_exclude = QAction("🚫 Excluded Paths from Anki Card Deletion", mw)
action_manage_delete_exclude.triggered.connect(
    lambda: open_exclude_manager(EXCLUDE_FROM_DELETE_FILE, "🚫 Excluded Paths from Anki Card Deletion")
)
mw.form.menuTools.addAction(action_manage_delete_exclude)

action_manage_sync_exclude = QAction("🚫 Excluded Paths from Sync", mw)
action_manage_sync_exclude.triggered.connect(
    lambda: open_exclude_manager(EXCLUDE_FROM_SYNC_FILE, "🚫 Excluded Paths from Sync")
)
mw.form.menuTools.addAction(action_manage_sync_exclude)

# ============================
# Helpers
# ============================
def normalize_id(node_id: str) -> str:
    if not node_id.startswith("ID_"):
        node_id = f"ID_{node_id}"
    return node_id

def normalize_pfile(pfile_url: str) -> str:
    if not pfile_url:
        return ""
    pfile_url = pfile_url.split("#")[0]
    prefix = "freeplane:/%20/"
    if pfile_url.startswith(prefix):
        pfile_url = pfile_url[len(prefix):]
    return os.path.normcase(os.path.normpath(pfile_url))

def get_ids_from_file(file_path):
    ids = set()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for node_elem in root.iter('node'):
            node = Node(tree, node_elem, file_path)
            if node.should_create_card():
                ids.add(node.get_node_id())
    except Exception as e:
        showInfo(f"Error reading file {file_path}:\n{e}")
    return ids

def is_excluded(pfile: str, exclude_file: str):
    pfile_norm = os.path.normcase(os.path.normpath(pfile))
    for excl in load_exclude_list(exclude_file):
        excl_norm = os.path.normcase(os.path.normpath(excl))
        if pfile_norm == excl_norm or pfile_norm.startswith(excl_norm + os.sep):
            return True
    return False

# ============================
# Remove old notes
# ============================
def remove_old_notes(mindmap_files: dict, base_folder: str = None, single_file_mode=False):
    model_name = "Freeplane basic"
    model = mw.col.models.byName(model_name)
    if not model:
        showInfo(f"Model '{model_name}' not found.")
        return 0

    mw.col.models.setCurrent(model)
    cids = mw.col.findNotes(f"mid:{model['id']}")
    notes = [mw.col.getNote(cid) for cid in cids]

    to_delete = []
    normalized_files = {os.path.normcase(os.path.normpath(fp)): ids for fp, ids in mindmap_files.items()}
    exclude_list_delete = [os.path.normcase(os.path.normpath(e)) for e in load_exclude_list(EXCLUDE_FROM_DELETE_FILE)]
    exclude_list_sync = [os.path.normcase(os.path.normpath(e)) for e in load_exclude_list(EXCLUDE_FROM_SYNC_FILE)]

    for note in notes:
        try:
            pfile = note["PFile"]
            node_id = note["ID"]
        except KeyError:
            continue

        if not pfile or not node_id:
            continue

        pfile_norm = normalize_pfile(pfile)
        node_id_norm = normalize_id(node_id)

        # ----------------------------
        # بررسی مسیر کارت نسبت به base_folder
        # ----------------------------
        if base_folder:
            base_norm = os.path.normcase(os.path.normpath(base_folder))
            if not single_file_mode:
                if not (pfile_norm.startswith(base_norm + os.sep) or pfile_norm == base_norm):
                    continue
            else:
                if pfile_norm not in normalized_files:
                    continue

        # ----------------------------
        # بررسی استثنا از حذف و استثنا از سینک
        # ----------------------------
        if any(pfile_norm == excl or pfile_norm.startswith(excl + os.sep) for excl in exclude_list_delete):
            continue  # از حذف کارت مستثنا

        if any(pfile_norm == excl or pfile_norm.startswith(excl + os.sep) for excl in exclude_list_sync):
            continue  # از کل سینک مستثنا

        # ----------------------------
        # بررسی حذف کارت
        # ----------------------------
        if not os.path.exists(pfile_norm):
            to_delete.append(note.id)
            continue

        ids_in_file = normalized_files.get(pfile_norm, set())
        if node_id_norm not in ids_in_file:
            to_delete.append(note.id)
            continue

    if to_delete:
        mw.col.remNotes(to_delete)
        mw.reset()

    return len(to_delete)

# ============================
# Import functions
# ============================
def importMindmapFromFile():
    file_path, _ = QFileDialog.getOpenFileName(
        caption="Select a .mm file", filter="Freeplane mindmap files (*.mm)"
    )
    if not file_path:
        return

    # بررسی استثنا از سینک
    if is_excluded(file_path, EXCLUDE_FROM_SYNC_FILE):
        showInfo(f"⚠️ File excluded from sync:\n{file_path}")
        return

    mindmap_files = {file_path: get_ids_from_file(file_path)}
    deleted_count = remove_old_notes(
        mindmap_files, base_folder=os.path.dirname(file_path), single_file_mode=True
    )

    importer = Importer(mw.col)
    reader = Reader()
    imported_notes = []
    updated_notes = []

    try:
        notes = reader.get_notes(ET.parse(file_path), file_path)
        for note in notes:
            note["PFile"] = file_path
            existing_notes = mw.col.findNotes(
                f'ID:{note["id"]} PFile:"{note["PFile"].replace("\\","\\\\")}"'
            )
            if existing_notes:
                existing_note = mw.col.getNote(existing_notes[0])
                fields_to_check = ["Front", "Back", "anki:deckbranch", "anki:deck", "BackLevels"]
                updated = False
                for field in fields_to_check:
                    note_value = str(note[field]).strip() if field in note else ""
                    existing_value = str(existing_note[field]).strip() if field in existing_note else ""
                    if note_value != existing_value:
                        updated = True
                        break
                if updated:
                    updated_notes.append(note["id"])
                importer.import_note(note)
            else:
                importer.import_note(note)
                imported_notes.append(note["id"])
    except Exception as e:
        showInfo(f"Error importing notes from file {file_path}:\n{e}")

    mw.reset()
    showInfo(
        f"🆕 {len(imported_notes)} notes imported\n"
        f"🔄 {len(updated_notes)} notes updated\n"
        f"🗑️ {deleted_count} notes deleted"
    )

def importMindmapFromFolder():
    folder = QFileDialog.getExistingDirectory(caption="Select a folder")
    if not folder:
        return

    # بررسی استثنا از سینک
    if is_excluded(folder, EXCLUDE_FROM_SYNC_FILE):
        showInfo(f"⚠️ Folder excluded from sync:\n{folder}")
        return

    mm_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".mm"):
                mm_files.append(os.path.join(root, file))

    if not mm_files:
        deleted_count = remove_old_notes({}, base_folder=folder)
        mw.reset()
        showInfo(
            f"📂 No .mm files found in folder or subfolders.\n"
            f"🗑️ {deleted_count} notes deleted"
        )
        return

    mindmap_files = {fp: get_ids_from_file(fp) for fp in mm_files}
    deleted_count = remove_old_notes(mindmap_files, base_folder=folder)

    importer = Importer(mw.col)
    reader = Reader()
    imported_notes = []
    updated_notes = []

    for file_path in mm_files:
        # بررسی استثنا از سینک فایل‌های داخلی
        if is_excluded(file_path, EXCLUDE_FROM_SYNC_FILE):
            continue

        try:
            notes = reader.get_notes(ET.parse(file_path), file_path)
            for note in notes:
                note["PFile"] = file_path
                existing_notes = mw.col.findNotes(
                    f'ID:{note["id"]} PFile:"{note["PFile"].replace("\\","\\\\")}"'
                )
                if existing_notes:
                    existing_note = mw.col.getNote(existing_notes[0])
                    fields_to_check = ["Front", "Back", "anki:deckbranch", "anki:deck", "BackLevels"]
                    updated = False
                    for field in fields_to_check:
                        note_value = str(note[field]).strip() if field in note else ""
                        existing_value = str(existing_note[field]).strip() if field in existing_note else ""
                        if note_value != existing_value:
                            updated = True
                            break
                    if updated:
                        updated_notes.append(note["id"])
                    importer.import_note(note)
                else:
                    importer.import_note(note)
                    imported_notes.append(note["id"])
        except Exception as e:
            showInfo(f"Error in file {file_path}:\n{e}")

    mw.reset()
    showInfo(
        f"🆕 {len(imported_notes)} notes imported\n"
        f"🔄 {len(updated_notes)} notes updated\n"
        f"🗑️ {deleted_count} notes deleted"
    )

# ============================
# Menu actions
# ============================
action_import_file = QAction("🔄 Sync Cards from Freeplane File", mw)
action_import_file.triggered.connect(importMindmapFromFile)
mw.form.menuTools.addAction(action_import_file)

action_import_folder = QAction("📂 Sync Cards from Folder (and Subfolders)", mw)
action_import_folder.triggered.connect(importMindmapFromFolder)
mw.form.menuTools.addAction(action_import_folder)
