"""
Cluedo Game Data - Constants and Configuration

Defines all game components:
- CHARACTERS: The 6 suspects
- WEAPONS: The 6 murder weapons
- ROOMS: The 9 rooms with grid positions
- SECRET_PASSAGES: Corner room connections
- START_POSITIONS: Where players begin
- ACCUSATION_SPOT: Center of the board
"""

CHARACTERS = [
    "Miss Scarlett",
    "Colonel Mustard",
    "Mrs. White",
    "Reverend Green",
    "Mrs. Peacock",
    "Professor Plum"
]

WEAPONS = [
    "Candlestick", "Dagger", "Lead Pipe",
    "Revolver", "Rope", "Wrench"
]

# 11x11 grid - ALL 9 ROOMS
# Layout:
#   S . . . . H . . . . L      (row 0)
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   l . . . . B . . . . D      (row 5) - Library, Billiard, Dining
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   C . . . . b . . . . K      (row 10)

ROOMS = {
    'Study': (0, 0),
    'Hall': (0, 5),
    'Lounge': (0, 10),
    'Library': (5, 0),
    'Billiard': (5, 5),
    'Dining': (5, 10),
    'Conservatory': (10, 0),
    'Ballroom': (10, 5),
    'Kitchen': (10, 10)
}

# Accusation spot (accusations can be made at any time, but this is still referenced in code)
# Moved to avoid conflict with Billiard room
ACCUSATION_SPOT = (6, 5)

SECRET_PASSAGES = {
    'Study': 'Kitchen',
    'Kitchen': 'Study',
    'Conservatory': 'Lounge',
    'Lounge': 'Conservatory'
}

# Short names for characters
CHARACTER_SHORT_NAMES = {
    "Miss Scarlett": "Scarlett",
    "Colonel Mustard": "Mustard",
    "Mrs. White": "White",
    "Reverend Green": "Green",
    "Mrs. Peacock": "Peacock",
    "Professor Plum": "Plum"
}

# Players start at random hallway positions (set at game initialization)

