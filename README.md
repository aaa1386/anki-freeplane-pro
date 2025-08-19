

# Anki-Freeplane Pro

Anki-Freeplane Pro is a plugin for the **Anki flashcard system** that converts **Freeplane/Freemind (.mm) mind maps** into Anki cards.
This plugin is developed based on [lajohnston/anki-freeplane (MIT)](https://github.com/lajohnston/anki-freeplane) by **aaa1386**.

## ✨ Features

1. **Card Syncing**
   Automatically creates and updates cards based on Freeplane nodes.
   If a card is deleted in Freeplane, it will also be deleted in Anki.
   Excluded Paths: files or folders can be marked so that their cards will never be deleted in Anki (explained below).

2. **File & Folder Support**
   Import a single `.mm` file → Import Cards from Freeplane
   Import all `.mm` files in a folder (recursive) → Import Cards from Folder

3. **Ancestor Path Display**
   Shows the ancestor path of each node.
   Helps visualize the exact position in the hierarchy.

4. **Navigate to Node**
   Click a node or its ancestor path in Anki to jump directly to the corresponding node in Freeplane.

5. **Back Card Outliner (up to 3 Levels)**
   The back of cards can display child nodes in an outline format.
   Outline depth limited to 3 levels → avoids infinite recursion.

## 💻 Installation / How to Install

There are two ways to install Anki-Freeplane Pro:

### From AnkiWeb

1. Go to [Anki-Freeplane Pro on AnkiWeb](https://ankiweb.net/shared/info/1554342344?cb=1755614751979).
2. Search for Anki-Freeplane Pro.
3. Follow the instructions on AnkiWeb to install the add-on directly into Anki.

### From GitHub Release

1. Go to [GitHub repository](https://github.com/aaa1386/anki-freeplane-pro).
2. Download the latest release (zip file).
3. Extract the zip file into Anki’s **add-ons folder**.
4. Restart Anki to activate the plugin.

## ⚠️ Important Setup Note

After installation, make sure to import the required card model:

• `note type.apkg` → import into Anki to create the required card model.
Based on Basic (needed for plugin).
Template name must stay the same, but some properties can be customized.

> This is crucial for displaying cards correctly in Anki. Make sure this step is done before importing any mind maps.

## 🃏 Card Creation & Deck Assignment

### Card Creation Rules

A node becomes a card only if it has at least one of these fields (even if empty):

• `anki:deckbranch`
• `anki:deck`
• `anki:model`

If none of these exist → the node is not converted into a card.
Child nodes of a card node are used as the back of the card (up to 3 levels).

**How to Add Fields:**

1. Right-click the node → Add Attribute
2. Enter field name (`anki:deckbranch`, `anki:deck`, or `anki:model`)
3. Optionally, enter a value (deck/model name)

### Deck Assignment Logic

1. If the current node has `anki:deckbranch` or `anki:deck` with a non-empty value → that value is used as the deck name.
2. If these fields are empty or missing → check ancestor nodes (closest parent upward).
3. Only ancestors with non-empty `anki:deckbranch` are considered; the first match is used.
4. If no valid value is found → default deck = FreeplaneDeck.

**Benefit:**

• Define a default deck for a whole subtree (e.g., `anki:deckbranch = Mathematics` on the root).
• Child cards inherit that deck unless explicitly overridden.
• Helps keep cards organized and prevents scattering.

## 🔧 Card Syncing & Management

• Cards are synced between Freeplane and Anki.
• If a node is deleted in Freeplane → its card is removed in Anki (unless excluded).

### Excluding Paths from Deletion

Using Manage Excluded Paths, you can mark files or folders so that their corresponding cards in Anki will never be deleted.

**Benefit:**

• You can dedicate an `.mm` file solely as a card generator.
• Cards will be created from that file.
• Even if nodes/cards are removed from the `.mm` file later, the cards in Anki will remain.

## 📦 Auxiliary Files & Tools

### Auxiliary Files Folder

• `ExampleMindmap.mm` → example mind map for testing.

### Tools Menu in Anki

• Import Cards from Freeplane → import a single `.mm` file.
• Import Cards from Folder → import all `.mm` files in a folder (recursive).
• Manage Excluded Paths → manage paths to exclude from card deletion.

می‌خوای این کار را انجام دهم؟
