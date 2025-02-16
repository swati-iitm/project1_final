# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    "json"
# ]
# ///
import json

# Load contacts from the JSON file
with open('./data/contacts.json', 'r') as file:
    contacts = json.load(file)

# Sort contacts by last_name and then first_name
contacts.sort(key=lambda c: (c['last_name'], c['first_name']))

# Save the sorted contacts to a new JSON file
with open('./data/contacts-sorted.json', 'w') as file:
    json.dump(contacts, file, indent=4)