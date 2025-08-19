# Anki Freeplane Importer Plugin

This is a plugin for the Anki flashcard system that allows you to convert Freeplane/Freemind .mm mindmaps into cards.

The plugin is currently a work in progress. The backend is working with unit tests, but does not yet have a user interface.

## Installation and example

This is just a proof-of-concept so far and only imports the mindmap found in the example directory. You can change this to point to a mindmap of your choice by editing the [mindmap.py](mindmap.py) file.

1. Copy this repository into the add-on directory (in Anki, click Tools > Add-ons > View files)
2. Restart Anki. You should now see 'Import mindmap' in the tools menu

# Freeplane Importer for Anki

This add-on allows you to import Freeplane mind maps directly into Anki.  
Each node in the mind map can be converted into a flashcard, with support 
for fields, attributes, and hierarchical card backs (up to 3 levels).

---

## Usage

1. Open Anki and go to:  
   **Tools → Import Cards from Freeplane**  
2. Select either:
   - A single Freeplane `.mm` file  
   - Or a folder (all `.mm` files inside, including subfolders, will be imported)  
3. Cards will be generated automatically.

---

## Card Creation Rule

A node will **only** be converted into a card if it contains **at least one** of these fields:

- `anki:deck`  
- `anki:model`  



 

---

## Notes

- Only nodes with the required fields are imported as cards.  
- Card backs are generated up to **3 nested levels** to prevent recursion.  

---


