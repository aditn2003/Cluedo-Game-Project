"""
Cluedo Board Display

Renders the 11x11 game board to the console.
Shows room positions, player locations, and game state.
"""

from data import ROOMS

# ANSI color codes
COLORS = {
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
    'DIM': '\033[2m',
    # Player colors (matching classic Cluedo character colors)
    'P1': '\033[91m',  # Red (Scarlett)
    'P2': '\033[93m',  # Yellow (Mustard)
    'P3': '\033[97m',  # White/Bright (White)
    'P4': '\033[92m',  # Green (Green)
    'P5': '\033[96m',  # Cyan (Peacock)
    'P6': '\033[95m',  # Magenta (Plum)
    # Other colors
    'ROOM': '\033[94m',  # Blue for room letters
    'HALLWAY': '\033[90m',  # Dark gray for hallway
    'ELIMINATED': '\033[91m\033[2m',  # Red + dim for eliminated
    'HEADER': '\033[1m',  # Bold for headers
}

ROOM_LETTERS = {
    'Study': 'S', 'Hall': 'H', 'Lounge': 'L',
    'Library': 'l', 'Billiard': 'B', 'Dining': 'D',
    'Conservatory': 'C', 'Ballroom': 'b', 'Kitchen': 'K'
}

GRID_SIZE = 11  # 11x11 grid

def colorize(text, color_code):
    """Add ANSI color code to text."""
    return f"{color_code}{text}{COLORS['RESET']}"

def get_player_color(player_num, eliminated=False):
    """Get color code for a player."""
    if eliminated:
        return COLORS['ELIMINATED']
    return COLORS.get(f'P{player_num}', COLORS['RESET'])

def format_player_token(player_num, eliminated=False):
    """Format player token with color."""
    prefix = 'X' if eliminated else 'P'
    token = f"{prefix}{player_num}"
    color = get_player_color(player_num, eliminated)
    return colorize(token, color)

def format_room_letter(letter):
    """Format room letter with color."""
    return colorize(letter, COLORS['ROOM'])

def format_player_name(player_name, player_num, eliminated=False):
    """Format player name with character color and colored token for use in messages."""
    # Color the player name based on their character color
    player_color = get_player_color(player_num, eliminated)
    colored_name = colorize(player_name, player_color)
    colored_token = format_player_token(player_num, eliminated)
    return f"{colored_name} ({colored_token})"

def show_board(players):
    print("\n" + "=" * 60)
    print("BOARD (11x11 Grid)")
    print("=" * 60)
    
    # Track who is in each room
    room_occupants = {room: [] for room in ROOMS.keys()}
    hallway_players = []
    
    for p in players:
        if p.get('in_room'):
            room_occupants[p['in_room']].append(p)
        else:
            hallway_players.append(p)
    
    # Build 11x11 grid
    grid = [['.' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Place room letters first
    for room, pos in ROOMS.items():
        r, c = pos
        occupants = room_occupants[room]
        if occupants:
            first = occupants[0]
            if first['eliminated']:
                grid[r][c] = 'X' + str(first['number'])
            else:
                grid[r][c] = 'P' + str(first['number'])
        else:
            grid[r][c] = ROOM_LETTERS[room]
    
    # Place hallway players (not in rooms)
    for p in hallway_players:
        r, c = p['position']
        if p['eliminated']:
            grid[r][c] = 'X' + str(p['number'])
        else:
            grid[r][c] = 'P' + str(p['number'])
    
    # Print column headers
    print("\n     ", end="")
    for c in range(GRID_SIZE):
        if c < 10:
            print(f" {c} ", end="")
        else:
            print(f"{c} ", end="")
    print("\n    " + "---" * GRID_SIZE)
    
    # Print grid
    for r in range(GRID_SIZE):
        if r < 10:
            print(f" {r} |", end="")
        else:
            print(f"{r} |", end="")
        for c in range(GRID_SIZE):
            cell = grid[r][c]
            if cell.startswith("P") or cell.startswith("X"):
                # Extract player number
                player_num = int(cell[1:])
                eliminated = cell.startswith("X")
                colored_token = format_player_token(player_num, eliminated)
                print(f" {colored_token}", end="")
            elif cell in ROOM_LETTERS.values():
                colored_letter = format_room_letter(cell)
                print(f" {colored_letter} ", end="")
            else:
                # Hallway dot
                dot = colorize(".", COLORS['HALLWAY'])
                print(f" {dot} ", end="")
        print()
    
    print("    " + "---" * GRID_SIZE)
    
    # WHO'S WHERE
    print("\n" + colorize("WHO'S WHERE:", COLORS['HEADER']))
    for room in ['Study', 'Hall', 'Lounge', 'Library', 'Billiard',
                 'Dining', 'Conservatory', 'Ballroom', 'Kitchen']:
        occupants = room_occupants.get(room, [])
        letter = format_room_letter(ROOM_LETTERS[room])
        if occupants:
            names = []
            for p in occupants:
                colored_name = colorize(p['name'], get_player_color(p['number'], p.get('eliminated')))
                colored_token = format_player_token(p['number'], p.get('eliminated'))
                tag = f"{colored_name} ({colored_token})"
                if p.get('is_ai'):
                    tag += "[AI]"
                if p.get('eliminated'):
                    tag += colorize("(out)", COLORS['DIM'])
                names.append(tag)
            print(f"  {letter}={room:12}: {', '.join(names)}")
        else:
            print(f"  {letter}={room:12}: (empty)")
    
    # Hallway players
    if hallway_players:
        names = []
        for p in hallway_players:
            colored_name = colorize(p['name'], get_player_color(p['number'], p.get('eliminated')))
            colored_token = format_player_token(p['number'], p.get('eliminated'))
            tag = f"{colored_name} ({colored_token})@({p['position'][0]},{p['position'][1]})"
            if p.get('is_ai'):
                tag += "[AI]"
            if p.get('eliminated'):
                tag += colorize("(out)", COLORS['DIM'])
            names.append(tag)
        print(f"  Hallway:        {', '.join(names)}")
    
    print("\n" + colorize("LEGEND:", COLORS['HEADER']))
    print("        Rooms: ", end="")
    room_colors = []
    for room, letter in ROOM_LETTERS.items():
        room_colors.append(f"{format_room_letter(letter)}={room}")
    print(", ".join(room_colors))
    print("        Players: ", end="")
    player_labels = []
    player_names = ['Scarlett', 'Mustard', 'White', 'Green', 'Peacock', 'Plum']
    for i in range(1, 7):
        colored_token = format_player_token(i)
        player_labels.append(f"{colored_token}={player_names[i-1]}")
    print(", ".join(player_labels))
    print(f"        {colorize('(Accusations can be made at any time during your turn!)', COLORS['DIM'])}")
