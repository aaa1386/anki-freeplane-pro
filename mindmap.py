import os
import xml.etree.ElementTree as ET
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import QAction, QFileDialog, QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox

from .freeplane_importer.model_not_found_exception import ModelNotFoundException
from .freeplane_importer.reader import Reader
from .freeplane_importer.importer import Importer

# فایل نگهداری مسیرهای استثنا
EXCLUDE_FROM_DELETE_FILE = os.path.join(os.path.dirname(__file__), "exclude_files.txt")

# ============================
# مدیریت مسیرهای استثنا
# ============================
def load_exclude_list():
    """بارگذاری مسیرهای استثنا از فایل"""
    if os.path.exists(EXCLUDE_FROM_DELETE_FILE):
        with open(EXCLUDE_FROM_DELETE_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_exclude_list(lst):
    """ذخیره مسیرهای استثنا در فایل"""
    with open(EXCLUDE_FROM_DELETE_FILE, "w", encoding="utf-8") as f:
        for item in lst:
            f.write(f"{item}\n")

class ExcludeManagerDialog(QDialog):
    """پنجره مدیریت مسیرهای استثنا"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Excluded Paths")
        self.resize(600, 400)

        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self.load_list()

        # دکمه‌ها
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
        """بارگذاری لیست مسیرهای استثنا در ویجت"""
        self.list_widget.clear()
        for path in load_exclude_list():
            self.list_widget.addItem(path)

    def add_file(self):
        """افزودن فایل به لیست استثنا"""
        file_path, _ = QFileDialog.getOpenFileName(caption="Select a file to exclude")
        if file_path:
            lst = load_exclude_list()
            if file_path not in lst:
                lst.append(file_path)
                save_exclude_list(lst)
                self.load_list()
                QMessageBox.information(self, "Success", f"File {file_path} added to exclude list.")

    def add_folder(self):
        """افزودن پوشه به لیست استثنا"""
        folder_path = QFileDialog.getExistingDirectory(caption="Select a folder to exclude")
        if folder_path:
            lst = load_exclude_list()
            if folder_path not in lst:
                lst.append(folder_path)
                save_exclude_list(lst)
                self.load_list()
                QMessageBox.information(self, "Success", f"Folder {folder_path} added to exclude list.")

    def remove_selected(self):
        """حذف مسیرهای انتخاب شده از لیست استثنا"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        lst = load_exclude_list()
        for item in selected_items:
            path = item.text()
            if path in lst:
                lst.remove(path)
        save_exclude_list(lst)
        self.load_list()
        QMessageBox.information(self, "Success", "Selected path(s) removed.")

def open_exclude_manager():
    dlg = ExcludeManagerDialog(mw)
    dlg.exec()

# افزودن گزینه مدیریت استثنا به منوی Tools
action_manage_exclude = QAction("🛡 Manage Excluded Paths", mw)
action_manage_exclude.triggered.connect(open_exclude_manager)
mw.form.menuTools.addAction(action_manage_exclude)

# ============================
# توابع کمکی
# ============================
def normalize_id(node_id: str) -> str:
    """حذف پیشوند ID_ از شناسه نود"""
    if node_id.startswith("ID_"):
        return node_id[3:]
    return node_id

def normalize_pfile(pfile_url: str) -> str:
    """تبدیل URL Freeplane به مسیر واقعی فایل"""
    if not pfile_url:
        return ""
    pfile_url = pfile_url.split("#")[0]
    prefix = "freeplane:/%20/"
    if pfile_url.startswith(prefix):
        pfile_url = pfile_url[len(prefix):]
    return os.path.normcase(os.path.normpath(pfile_url))

def get_ids_from_file(file_path):
    """دریافت مجموعه شناسه‌های نودها از یک فایل .mm"""
    ids = set()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for node in root.iter('node'):
            node_id = node.attrib.get('ID')
            if node_id:
                ids.add(normalize_id(node_id))
    except Exception as e:
        showInfo(f"Error reading file {file_path}:\n{e}")
    return ids

def is_excluded(pfile: str):
    """بررسی اینکه مسیر در لیست استثنا هست یا خیر"""
    pfile_norm = os.path.normcase(os.path.normpath(pfile))
    for excl in load_exclude_list():
        excl_norm = os.path.normcase(os.path.normpath(excl))
        if pfile_norm == excl_norm or pfile_norm.startswith(excl_norm + os.sep):
            return True
    return False

# ============================
# حذف کارت‌های قدیمی
# ============================
def remove_old_notes(mindmap_files: dict):
    """
    حذف کارت‌های قدیمی قبل از وارد کردن کارت‌های جدید
    کارت حذف می‌شود اگر:
    - مسیر PFile کارت در فایل‌های انتخاب شده باشد
    - و ID نود کارت در فایل مربوطه وجود نداشته باشد
    """
    model_name = "Freeplane basic"
    model = mw.col.models.byName(model_name)
    if not model:
        showInfo(f"Model '{model_name}' not found.")
        return 0

    # اطمینان از انتخاب مدل صحیح
    mw.col.models.setCurrent(model)

    cids = mw.col.findNotes(f"mid:{model['id']}")
    notes = [mw.col.getNote(cid) for cid in cids]

    to_delete = []
    normalized_files = {os.path.normcase(os.path.normpath(fp)): ids for fp, ids in mindmap_files.items()}

    for note in notes:
        pfile = note["PFile"] if "PFile" in note else None
        node_id = note["ID"] if "ID" in note else None
        if not pfile or not node_id:
            continue
        pfile_norm = normalize_pfile(pfile)
        if is_excluded(pfile_norm):
            continue
        if pfile_norm not in normalized_files:
            continue
        node_id = normalize_id(node_id)
        if node_id not in normalized_files[pfile_norm]:
            to_delete.append(note.id)

    if to_delete:
        mw.col.remNotes(to_delete)
        mw.reset()
    return len(to_delete)

# ============================
# وارد کردن کارت‌ها
# ============================
def importMindmapFromFile():
    """وارد کردن کارت‌ها از یک فایل .mm"""
    file_path, _ = QFileDialog.getOpenFileName(caption="Select a .mm file", filter="Freeplane mindmap files (*.mm)")
    if not file_path:
        return

    mindmap_files = {file_path: get_ids_from_file(file_path)}
    deleted = remove_old_notes(mindmap_files)
    if deleted:
        showInfo(f"{deleted} old notes removed.")

    importer = Importer(mw.col)
    reader = Reader()
    total_imported = 0
    try:
        notes = reader.get_notes(ET.parse(file_path), file_path)
        for note in notes:
            note["PFile"] = file_path
            try:
                importer.import_note(note)
            except ModelNotFoundException as e:
                showInfo(f"Model not found: {e.model_name}")
        total_imported += len(notes)
    except Exception as e:
        showInfo(f"Error importing notes from file {file_path}:\n{e}")

    mw.reset()
    showInfo(f"{total_imported} notes imported from file.")

def importMindmapFromFolder():
    """وارد کردن کارت‌ها از پوشه و زیرپوشه‌ها"""
    folder = QFileDialog.getExistingDirectory(caption="Select a folder")
    if not folder:
        return

    mm_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".mm"):
                mm_files.append(os.path.join(root, file))
    if not mm_files:
        showInfo("No .mm files found in folder or subfolders.")
        return

    mindmap_files = {fp: get_ids_from_file(fp) for fp in mm_files}
    deleted = remove_old_notes(mindmap_files)
    if deleted:
        showInfo(f"{deleted} old notes removed.")

    importer = Importer(mw.col)
    reader = Reader()
    total_imported = 0
    for file_path in mm_files:
        try:
            notes = reader.get_notes(ET.parse(file_path), file_path)
            for note in notes:
                note["PFile"] = file_path
                try:
                    importer.import_note(note)
                except ModelNotFoundException as e:
                    showInfo(f"Model not found: {e.model_name}")
            total_imported += len(notes)
        except Exception as e:
            showInfo(f"Error in file {file_path}:\n{e}")

    mw.reset()
    showInfo(f"{total_imported} notes imported from {len(mm_files)} files.")

# ============================
# افزودن گزینه‌ها به منوی Tools
# ============================
action_import_file = QAction("📄 Import Mindmap from File", mw)
action_import_file.triggered.connect(importMindmapFromFile)
mw.form.menuTools.addAction(action_import_file)

action_import_folder = QAction("📂 Import Mindmaps from Folder (and Subfolders)", mw)
action_import_folder.triggered.connect(importMindmapFromFolder)
mw.form.menuTools.addAction(action_import_folder)
