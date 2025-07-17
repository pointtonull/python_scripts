#!/usr/bin/env python

import keyring

import gkeepapi

keep = gkeepapi.Keep()

# Create a new note
note = keep.createNote("Todo", "Buy groceries")

# Search for notes
notes = keep.find(query="Shopping list")

# Update a note
note.text = "Buy groceries and milk"
keep.sync()  # Sync changes to server
