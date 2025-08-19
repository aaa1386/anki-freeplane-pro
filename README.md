# Anki-Freeplane Pro

Anki-Freeplane Pro is a plugin for the Anki flashcard system that allows you to convert Freeplane/Freemind (.mm) mind maps into Anki cards.  
This plugin is developed based on [lajohnston/anki-freeplane (MIT)](https://github.com/lajohnston/anki-freeplane) by **aaa1386**.

---

## 1. Plugin Features

1. **Card Syncing**
   - The plugin syncs cards with Freeplane.
   - If a card is deleted in Freeplane, it will also be removed from Anki.
   - Cards are automatically created and updated during sync.
   - The **Manage Excluded Paths** option allows you to exclude certain files or paths from being deleted in Anki.

2. **Support for Files and Folders**
   - **Import Cards from Freeplane** → import a single `.mm` file  
   - **Import Cards from Folder** → import all `.mm` files in a folder and its subfolders

3. **Excluding Paths from Deletion**
   - Using **Manage Excluded Paths**, you can mark files or folders to prevent their cards from being deleted in Anki.

حتماً ✅ این متن انگلیسیِ جدا برای هر کدوم:

 4. ** Ancestor Path Display**

   * The ancestor path of each node in Freeplane can be viewed.
   * This helps users clearly see the node’s exact position in the hierarchy and better understand relationships between nodes.



5. ** Navigate to Node**

   * Users can click on a node or any part of its ancestor path.
   * This action takes them directly to the corresponding node in Freeplane.


6. Back Card Outliner (Up to Three Levels)
   •	The back side of a card can display child nodes in an outliner format.
   •	The outline view is limited to three levels of depth to keep the content clear and avoid infinite recursion.
   •	This helps users review hierarchical information in a structured way directly on the card.


---

## 2. Card Creation Rules in Freeplane

A node will only be converted into a card if it has at least one of the following fields, even if the value is empty:

- `anki:deckbranch`
- `anki:deck`
- `anki:model`

If none of these fields exist, the node will not be converted into a card.  
Missing or empty fields do not cause issues, but at least one field is required.  
Child nodes of a card node are used as the back of the Anki card up to 3 levels deep.

### How to Add Fields

- You can add these fields using **Attributes** in Freeplane:
  1. Right-click the node → **Add Attribute**
  2. Enter the field name (`anki:deckbranch`, `anki:deck`, or `anki:model`)
  3. Optionally, enter a value for the deck or model.

---

## 3. Using the Plugin (Card Syncing)

- The plugin provides card syncing functionality.
- If a card is deleted in Freeplane but still exists in Anki, it will be deleted in the next sync.
- The **Manage Excluded Paths** option allows you to exclude files or paths so that cards from them are not deleted.

### How to Use

1. In Anki, go to **Tools** and open the plugin options.
2. Choose one of the options:
   - **Import Cards from Freeplane** → import a single `.mm` file
   - **Import Cards from Folder** → import all `.mm` files in a folder and its subfolders
3. Cards are automatically created or updated (synced).

---

## 4. Auxiliary Files Folder

- The **Auxiliary files** folder contains helper files:
  - `note type.apkg` → import this file into Anki to create the card model
    - Important: This card model is based on **Basic** and is essential for the plugin to function correctly.
    - Do not change the template name, but some properties can be adjusted or customized.
  - `ExampleMindmap.mm` → example mind map for testing the plugin

---

## 5. Tools Menu in Anki

Currently, there are three options:

1. **Import Cards from Freeplane**
   - Import a single `.mm` file

2. **Import Cards from Folder**
   - Import all `.mm` files in a folder and its subfolders

3. **Manage Excluded Paths**
   - Manage paths you want to exclude from card creation or deletion

---

## 6.##  Card Deck Assignment Rules  

Cards can be assigned to decks either automatically or manually. The main rules are as follows:  

### 1. Using the `anki:deckbranch` attribute in the node:  
- If it has a value → it will be used as the deck name  
- If it is empty → the card will automatically be placed in the default **FreeplaneDeck**  

### 2. Using `anki:deck` in the node:  
- If the field exists and has a value → its value will be used as the deck name  
- If the field has no value → ancestors will be checked:  

**Checking the node's ancestors**  
- If an ancestor has the `anki:deckbranch` field:  
  - If a value is set → its value will be used for the deck name  
  - If the value is empty → it will be assigned to **FreeplaneDeck**  
- If no ancestor with the `anki:deckbranch` field is found → assigned to **FreeplaneDeck**  


