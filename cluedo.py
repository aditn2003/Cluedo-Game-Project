"""
Cluedo Game Engine

Main game class that handles:
- Game initialization and setup
- Turn management for human and AI players
- Suggestions and refutations
- Accusations and win conditions
- Player movement and room interactions
"""

import random
import time
from data import CHARACTERS, WEAPONS, ROOMS, SECRET_PASSAGES, ACCUSATION_SPOT, CHARACTER_SHORT_NAMES
from board import show_board, format_player_token, format_player_name, COLORS, colorize, get_player_color
from ai_player import AIPlayer

class SimpleCluedo:
    def __init__(self, debug=False):
        self.debug = debug
        self.grid_size = 11  # 11x11 grid
        
        # Ask how many players
        print("=" * 60)
        print("SIMPLE CLUEDO - 9x9 GRID")
        print("=" * 60)
        
        while True:
            try:
                num = input("\nHow many players? (2-6): ").strip()
                num_players = int(num)
                if 2 <= num_players <= 6:
                    break
                print("Please enter a number between 2 and 6.")
            except ValueError:
                print("Please enter a valid number.")
        
        self.num_players = num_players
        
        # Ask about AI player
        ai_choice = input("\nShould Player 1 be an AI? (y/n): ").strip().lower()
        self.has_ai = ai_choice in ['y', 'yes']
        
        self.players = []
        # Generate random starting positions (hallway only, not rooms)
        used_positions = set()
        for i in range(num_players):
            # Find a random hallway position
            attempts = 0
            while attempts < 100:
                r = random.randint(0, 10)
                c = random.randint(0, 10)
                pos = (r, c)
                # Not a room, not center, not occupied
                if pos not in ROOMS.values() and pos != ACCUSATION_SPOT and pos not in used_positions:
                    used_positions.add(pos)
                    break
                attempts += 1
            else:
                # Fallback to center if can't find position
                pos = ACCUSATION_SPOT
            
            self.players.append({
                'name': CHARACTERS[i],
                'number': i + 1,
                'position': pos,
                'cards': [],
                'eliminated': False,
                'cards_seen': [],
                'in_room': None,
                'was_dragged': False,
                'has_accused': False,  # Only ONE accusation allowed per player
                'is_ai': (i == 0 and self.has_ai)  # P1 is AI if chosen
            })
        
        self.solution = self._setup_solution()
        
        # Create AI player controller if needed
        self.ai_controller = None
        if self.has_ai:
            self.ai_controller = AIPlayer(
                player_number=1, 
                num_players=num_players,
                player_data=self.players[0]
            )
            # Give AI its cards
            self.ai_controller.receive_cards(self.players[0]['cards'])
        self.current_player = 0
        self.eliminated_count = 0
        self.weapon_positions = {w: None for w in WEAPONS}
        self.game_over = False  # Tracks if game has ended
        
        print(f"\n{num_players} Players:")
        for p in self.players:
            ai_tag = " [AI]" if p.get('is_ai') else ""
            colored_name_token = format_player_name(p['name'], p['number'], p.get('eliminated'))
            print(f"  {colored_name_token}{ai_tag}")
        print("\n" + "=" * 60)
        print("HOW TO WIN:")
        print("=" * 60)
        print("1. Make SUGGESTIONS to gather clues")
        print("2. Others will show you cards they have")
        print("3. DEDUCE what's NOT in the solution")
        print("4. When you know the answer, make an ACCUSATION")
        print(f"5. Correct accusation = {colorize('YOU WIN!', '\033[92m\033[1m')}")
        print(f"6. Wrong accusation = {colorize('YOU\'RE ELIMINATED!', '\033[91m\033[1m')}")
        print("=" * 60)
        print("\nThe solution has been sealed in an envelope...")
        print("(3 cards: 1 character, 1 weapon, 1 room)")
        
        # Show solution if debug mode is enabled
        if self.debug:
            print("\n" + "=" * 60)
            print("[DEBUG] SOLUTION (FOR TESTING ONLY):")
            print("=" * 60)
            print(f"  Character: {self.solution['character']}")
            print(f"  Weapon:    {self.solution['weapon']}")
            print(f"  Room:      {self.solution['room']}")
            print("=" * 60)

    def _setup_solution(self):
        solution = {
            'character': random.choice(CHARACTERS),
            'weapon': random.choice(WEAPONS),
            'room': random.choice(list(ROOMS.keys()))
        }
        remaining = []
        for c in CHARACTERS:
            if c != solution['character']:
                remaining.append(('character', c))
        for w in WEAPONS:
            if w != solution['weapon']:
                remaining.append(('weapon', w))
        for r in ROOMS.keys():
            if r != solution['room']:
                remaining.append(('room', r))
        random.shuffle(remaining)
        
        # Deal cards evenly to players
        for i, card in enumerate(remaining):
            self.players[i % self.num_players]['cards'].append(card)
        
        return solution

    def get_room_at(self, r, c):
        for room, pos in ROOMS.items():
            if pos == (r, c):
                return room
        return None

    def get_valid_moves(self, player):
        r, c = player['position']
        moves = []
        dirs = [
            ('U', 'UP', r - 1, c),
            ('D', 'DOWN', r + 1, c),
            ('L', 'LEFT', r, c - 1),
            ('R', 'RIGHT', r, c + 1)
        ]
        for short, long, nr, nc in dirs:
            if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                room = self.get_room_at(nr, nc)
                if room:
                    moves.append(f"{short}/{long} -> {room}")
                else:
                    # Check if hallway space is occupied
                    occupied = False
                    for p in self.players:
                        if p != player and p['position'] == (nr, nc) and not p['eliminated']:
                            occupied = True
                            break
                    if occupied:
                        moves.append(f"{short}/{long} (BLOCKED)")
                    else:
                        moves.append(f"{short}/{long}")
        return moves

    def is_hallway_occupied(self, r, c):
        """Check if a hallway space is occupied by another player."""
        # Rooms can have multiple players, hallways cannot
        if self.get_room_at(r, c):
            return False  # It's a room, no collision check needed
        for p in self.players:
            if p['position'] == (r, c) and not p['eliminated']:
                return True
        return False
    
    def move_player(self, player, direction):
        r, c = player['position']
        d = direction.upper()
        if d in ['U', 'UP']:
            nr, nc = r - 1, c
        elif d in ['D', 'DOWN']:
            nr, nc = r + 1, c
        elif d in ['L', 'LEFT']:
            nr, nc = r, c - 1
        elif d in ['R', 'RIGHT']:
            nr, nc = r, c + 1
        else:
            return False
        if nr < 0 or nr >= self.grid_size or nc < 0 or nc >= self.grid_size:
            print("Out of bounds!")
            return False
        
        # Check hallway collision (rooms and center can have multiple players)
        room_at_dest = self.get_room_at(nr, nc)
        is_center = (nr, nc) == ACCUSATION_SPOT
        if not room_at_dest and not is_center:  # It's a hallway space
            for p in self.players:
                if p != player and p['position'] == (nr, nc) and not p['eliminated']:
                    # Don't print here - error will be shown during batch validation
                    return False
        
        player['position'] = (nr, nc)
        return True

    def show_cards(self, player):
        print(f"\n{player['name']} (P{player['number']})'s Cards:")
        chars = [name for t, name in player['cards'] if t == 'character']
        weps = [name for t, name in player['cards'] if t == 'weapon']
        rms = [name for t, name in player['cards'] if t == 'room']
        print("  Characters:", ", ".join(chars) if chars else "None")
        print("  Weapons:", ", ".join(weps) if weps else "None")
        print("  Rooms:", ", ".join(rms) if rms else "None")
        if player['cards_seen']:
            print("  Cards You've Seen (from others):", ", ".join(player['cards_seen']))
        self.show_deduction_helper(player)
    
    def show_deduction_helper(self, player):
        """Show deduction helper - possible solution cards."""
        print("\n  DEDUCTION HELPER:")
        known = set([name for _, name in player['cards']] + player['cards_seen'])
        unk_c = [c for c in CHARACTERS if c not in known]
        unk_w = [w for w in WEAPONS if w not in known]
        unk_r = [r for r in ROOMS.keys() if r not in known]
        # Use short names for characters
        unk_c_short = [CHARACTER_SHORT_NAMES.get(c, c) for c in unk_c]
        print("     Possible Characters:", ", ".join(unk_c_short) if unk_c_short else "DEDUCED!")
        print("     Possible Weapons:", ", ".join(unk_w) if unk_w else "DEDUCED!")
        print("     Possible Rooms:", ", ".join(unk_r) if unk_r else "DEDUCED!")
        if len(unk_c) == 1 and len(unk_w) == 1 and len(unk_r) == 1:
            print("\n  YOU'VE DEDUCED THE SOLUTION!")
            print("     Make an accusation!")
    
    def _get_full_character_name(self, name_input):
        """Convert short name or full name to full character name. Returns None if invalid."""
        name_input = name_input.strip()
        # Check if it's already a full name
        if name_input in CHARACTERS:
            return name_input
        # Check if it's a short name
        for full_name, short_name in CHARACTER_SHORT_NAMES.items():
            if name_input.lower() == short_name.lower():
                return full_name
        # Try case-insensitive match
        for full_name in CHARACTERS:
            if name_input.lower() in full_name.lower():
                return full_name
        return None  # Invalid input
    
    def _normalize_weapon(self, weapon_input):
        """Normalize weapon input to match actual weapon names (case-insensitive). Returns None if invalid."""
        weapon_input = weapon_input.strip()
        # Check exact match first
        if weapon_input in WEAPONS:
            return weapon_input
        # Try case-insensitive match
        for weapon in WEAPONS:
            if weapon_input.lower() == weapon.lower():
                return weapon
        return None  # Invalid input
    
    def _normalize_room(self, room_input):
        """Normalize room input to match actual room names (case-insensitive). Returns None if invalid."""
        room_input = room_input.strip()
        # Check exact match first
        if room_input in ROOMS:
            return room_input
        # Try case-insensitive match
        for room in ROOMS:
            if room_input.lower() == room.lower():
                return room
        return None  # Invalid input

    def make_suggestion(self, player, character, weapon, room):
        # Use short name for display
        char_short = CHARACTER_SHORT_NAMES.get(character, character)
        colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
        print(f"\n{colored_name_token} suggests:")
        print(f"  -> {char_short}, with the {weapon}, in the {room}")
        
        # Drag character if not self
        for p in self.players:
            if p['name'] == character and not p['eliminated']:
                if p != player:  # Don't drag yourself
                    prev = p['position']
                    p['in_room'] = room
                    p['position'] = ROOMS[room]
                    p['was_dragged'] = True  # Can suggest without moving on their turn
                    char_short = CHARACTER_SHORT_NAMES.get(character, character)
                    colored_name_token = format_player_name(p['name'], p['number'], p.get('eliminated'))
                    print(f"  -> {colored_name_token} dragged to {room}")
                break
        
        # Move weapon
        prev_weapon = self.weapon_positions.get(weapon)
        self.weapon_positions[weapon] = room
        if prev_weapon:
            print(f"  -> {weapon} moved from {prev_weapon} to {room}")
        else:
            print(f"  -> {weapon} placed in {room}")
        
        items = [character, weapon, room]
        players_who_passed = []
        refuter = None
        card_shown = None
        
        # Clockwise refutation (eliminated players CAN still refute!)
        for i in range(1, self.num_players):
            idx = (self.current_player + i) % self.num_players
            other = self.players[idx]
            # Note: Eliminated players can still show cards to refute!
            
            # Check if other has any matching cards
            matching_cards = [name for t, name in other['cards'] if name in items]
            
            if matching_cards:
                refuter = other
                
                # AI refutation: choose card strategically
                if other.get('is_ai') and self.ai_controller:
                    card_shown = self.ai_controller.choose_card_to_show(
                        (character, weapon, room), matching_cards
                    )
                    if other['eliminated']:
                        eliminated_tag = colorize(" (ELIMINATED)", COLORS['ELIMINATED'])
                    else:
                        eliminated_tag = ""
                    colored_name_token = format_player_name(other['name'], other['number'], other['eliminated'])
                    print(f"\n  {colored_name_token} [AI]{eliminated_tag} refutes with a card!")
                    # Only suggester sees the card
                    if player.get('is_ai'):
                        print(f"  [AI sees: {card_shown}]")
                    else:
                        print(f"  [Only you see: {card_shown}]")
                else:
                    # Human refutation
                    if other['eliminated']:
                        eliminated_tag = colorize(" (ELIMINATED)", COLORS['ELIMINATED'])
                    else:
                        eliminated_tag = ""
                    colored_name_token = format_player_name(other['name'], other['number'], other['eliminated'])
                    print(f"\n  {colored_name_token}{eliminated_tag} can refute!")
                    
                    if len(matching_cards) == 1:
                        # Auto-select if only one matching card
                        card_shown = matching_cards[0]
                        print(f"  [Auto-selected: {card_shown} (only one matching card)]")
                    else:
                        # Ask which card to show if multiple
                        print(f"  P{other['number']}, choose a card to show:")
                        for i, card in enumerate(matching_cards, 1):
                            print(f"    {i}. {card}")
                        while True:
                            choice = input("  Enter number: ").strip()
                            try:
                                idx = int(choice) - 1
                                if 0 <= idx < len(matching_cards):
                                    card_shown = matching_cards[idx]
                                    break
                            except ValueError:
                                pass
                            print("  Invalid choice, try again.")
                    
                    colored_name_token = format_player_name(other['name'], other['number'], other['eliminated'])
                    print(f"\n  {colored_name_token}{eliminated_tag} refutes with a card!")
                    if player.get('is_ai'):
                        print(f"  [AI sees: {card_shown}]")
                    else:
                        print(f"  [Only you see: {card_shown}]")
                
                # Record seen card
                if card_shown not in player['cards_seen']:
                    player['cards_seen'].append(card_shown)
                
                break  # Stop after first refutation
            else:
                players_who_passed.append(other['number'])
        
        # Update AI knowledge
        if self.ai_controller:
            if refuter:
                self.ai_controller.observe_suggestion(
                    suggester=player['number'],
                    character=character, weapon=weapon, room=room,
                    refuter=refuter['number'],
                    card_shown=card_shown if player.get('is_ai') else None,  # AI only sees if it suggested
                    players_who_passed=players_who_passed
                )
            else:
                self.ai_controller.observe_suggestion(
                    suggester=player['number'],
                    character=character, weapon=weapon, room=room,
                    refuter=None, card_shown=None,
                    players_who_passed=players_who_passed
                )
        
        if not refuter:
            warning_color = '\033[93m\033[1m'  # Bright yellow for warning
            print(f"\n  {colorize('NO ONE CAN REFUTE!', warning_color)}")
            print(f"  {colorize('This combination might be the solution!', COLORS['BOLD'])}")
            print(f"  {colorize('(Note: Eliminated players can still refute if they have matching cards)', COLORS['DIM'])}")

    def make_accusation(self, player, character, weapon, room):
        # Color definitions
        win_color = '\033[92m\033[1m'  # Bright green for wins
        error_color = '\033[91m\033[1m'  # Bright red for errors
        
        print("\n" + "=" * 50)
        colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
        print(f"{colored_name_token} ACCUSES:")
        print(f"  {character}, with the {weapon}, in the {room}")
        print("=" * 50)
        correct = (
            character == self.solution['character'] and
            weapon == self.solution['weapon'] and
            room == self.solution['room']
        )
        if correct:
            # Winning messages - Green/Bright colors
            colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
            print(f"\n{colorize('CORRECT!', win_color)} {colored_name_token} {colorize('WINS!', win_color)}")
            print(f"\n{colorize('The solution was:', COLORS['BOLD'])}")
            print(f"  {colorize('Character:', COLORS['BOLD'])} {character}")
            print(f"  {colorize('Weapon:', COLORS['BOLD'])}    {weapon}")
            print(f"  {colorize('Room:', COLORS['BOLD'])}      {room}")
            print("\n" + "=" * 50)
            print(f"{colorize('GAME OVER', COLORS['BOLD'])} - {colored_name_token} {colorize('solved the mystery!', win_color)}")
            print("=" * 50)
            return True
        else:
            # Elimination messages - Red colors
            colored_name_token = format_player_name(player['name'], player['number'], eliminated=True)
            print(f"\n{colorize('WRONG!', error_color)} {colored_name_token} {colorize('is ELIMINATED!', error_color)}")
            print(colorize("(The solution remains secret)", COLORS['DIM']))
            player['eliminated'] = True
            active = [p for p in self.players if not p['eliminated']]
            if len(active) == 1:
                print("\n" + "=" * 50)
                winner = active[0]
                winner_name_token = format_player_name(winner['name'], winner['number'], winner.get('eliminated'))
                print(f"{winner_name_token} {colorize('is the only player left!', COLORS['BOLD'])}")
                print(f"{winner_name_token} {colorize('WINS by default!', win_color)}")
                print("=" * 50)
                return True
            elif len(active) == 0:
                print("\n" + "=" * 50)
                print(colorize("All players eliminated! No winner!", error_color + COLORS['DIM']))
                print("=" * 50)
                return True
            return False

    def handle_room_entry(self, player, room):
        """Called when player ENTERS a room - MUST make suggestion."""
        player['was_dragged'] = False
        player['in_room'] = room
        colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
        print(f"\n{colored_name_token} entered {room}.")
        print("You MUST make a suggestion!")
        
        # Show deduction helper BEFORE making suggestion (mandatory, so no y/n)
        self.show_deduction_helper(player)
        
        print(f"\nSuggestion is about: WHO did it, with WHAT weapon, in {room}")
        # Use short names for characters
        short_names = [CHARACTER_SHORT_NAMES.get(c, c) for c in CHARACTERS]
        print("\nCharacters:", ", ".join(short_names))
        
        # Validate character input
        while True:
            c_input = input("Who? ").strip()
            c = self._get_full_character_name(c_input)
            if c is not None:
                break
            print(f"Invalid character. Please enter one of: {', '.join(short_names)}")
        
        print("\nWeapons:", ", ".join(WEAPONS))
        
        # Validate weapon input
        while True:
            w_input = input("Weapon? ").strip()
            w = self._normalize_weapon(w_input)
            if w is not None:
                break
            print(f"Invalid weapon. Please enter one of: {', '.join(WEAPONS)}")
        
        self.make_suggestion(player, c, w, room)
    
    
    def offer_accusation(self, player):
        """Offer player the chance to make an accusation (can be done anytime)."""
        if player['has_accused']:
            return False  # Already used their one accusation
        
        print("\n" + "-" * 40)
        print("You may make ONE ACCUSATION per game.")
        win_hint = colorize("WIN!", '\033[92m')
        elim_hint = colorize("ELIMINATED!", '\033[91m')
        print(f"Correct = {win_hint} Wrong = {elim_hint}")
        print("-" * 40)
        acc = input("Make an ACCUSATION now? (y/n): ").strip().lower()
        
        if acc in ['y', 'yes']:
            player['has_accused'] = True
            print("\n*** ACCUSATION - Get it right or you're OUT! ***")
            # Use short names for characters
            short_names = [CHARACTER_SHORT_NAMES.get(c, c) for c in CHARACTERS]
            print("\nCharacters:", ", ".join(short_names))
            
            # Validate character input
            while True:
                c_input = input("WHO did it? ").strip()
                c = self._get_full_character_name(c_input)
                if c is not None:
                    break
                print(f"Invalid character. Please enter one of: {', '.join(short_names)}")
            
            print("\nWeapons:", ", ".join(WEAPONS))
            
            # Validate weapon input
            while True:
                w_input = input("With WHAT weapon? ").strip()
                w = self._normalize_weapon(w_input)
                if w is not None:
                    break
                print(f"Invalid weapon. Please enter one of: {', '.join(WEAPONS)}")
            
            print("\nRooms:", ", ".join(ROOMS.keys()))
            
            # Validate room input
            while True:
                r_input = input("In WHICH room? ").strip()
                r = self._normalize_room(r_input)
                if r is not None:
                    break
                print(f"Invalid room. Please enter one of: {', '.join(ROOMS.keys())}")
            if self.make_accusation(player, c, w, r):
                self.game_over = True
                return True
            return True  # Accusation was made (even if wrong)
        return False  # No accusation made

    def play_turn(self):
        player = self.players[self.current_player]
        if player['eliminated']:
            colored_name_token = format_player_name(player['name'], player['number'], eliminated=True)
            eliminated_msg = colorize("is eliminated - skipping turn.", COLORS['ELIMINATED'])
            print(f"\n{colored_name_token} {eliminated_msg}")
            return
        
        # Check if this is an AI turn
        if player.get('is_ai') and self.ai_controller:
            self._play_ai_turn(player)
            return
        
        # Human turn
        print("\n" + "=" * 60)
        colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
        print(f"TURN: {colored_name_token}")
        print("=" * 60)
        show_board(self.players)
        r, c = player['position']
        if player['in_room']:
            print(f"\nYou are in: {player['in_room']}")
        else:
            print(f"\nYour position: ({r}, {c}) - In hallway")
        self.show_cards(player)
        
        # ACCUSATION OPTION - Can be made at ANY point (once per game)
        if not player['has_accused']:
            if self.offer_accusation(player):
                if self.game_over:
                    return
                # If they made a wrong accusation, they're eliminated
                if player['eliminated']:
                    return
        
        # Track if suggestion was made this turn (only 1 per turn)
        suggestion_made = False
        
        # If player was dragged to a room, OPTIONAL suggestion (not mandatory)
        if player['in_room'] and player.get('was_dragged'):
            print("\n*** You were dragged here by another player's suggestion! ***")
            print(f"You are in: {player['in_room']}")
            room = player['in_room']
            player['was_dragged'] = False  # Clear the flag
            
            # Show deduction helper
            self.show_deduction_helper(player)
            
            # Ask if they want to make a suggestion (optional)
            sug = input("\nMake a SUGGESTION? (y/n): ").strip().lower()
            if sug in ['y', 'yes']:
                suggestion_made = True
                print(f"\nSuggestion is about: WHO did it, with WHAT weapon, in {room}")
                # Use short names for characters
                short_names = [CHARACTER_SHORT_NAMES.get(c, c) for c in CHARACTERS]
                print("\nCharacters:", ", ".join(short_names))
                
                # Validate character input
                while True:
                    c_input = input("Who? ").strip()
                    c = self._get_full_character_name(c_input)
                    if c is not None:
                        break
                    print(f"Invalid character. Please enter one of: {', '.join(short_names)}")
                
                print("\nWeapons:", ", ".join(WEAPONS))
                
                # Validate weapon input
                while True:
                    w_input = input("Weapon? ").strip()
                    w = self._normalize_weapon(w_input)
                    if w is not None:
                        break
                    print(f"Invalid weapon. Please enter one of: {', '.join(WEAPONS)}")
                
                self.make_suggestion(player, c, w, room)
                # After suggestion, exit room and continue to dice roll (they can still move)
                player['in_room'] = None
            else:
                print("You chose not to suggest.")
                # Exit room to allow movement
                player['in_room'] = None
            # Continue to dice roll below (don't return)
        
        # If turn starts in a room (but wasn't dragged), NO suggestion - must exit first
        elif player['in_room']:
            print(f"\nYou are in: {player['in_room']}")
            print("You cannot make a suggestion when starting in a room.")
            print("You must exit the room first.")
            # SECRET PASSAGE option (using secret passage counts as entering)
            if player['in_room'] in SECRET_PASSAGES:
                dest = SECRET_PASSAGES[player['in_room']]
                print(f"\n*** Secret passage to {dest} available! ***")
                use = input(f"Use secret passage to {dest}? (y/n): ").strip().lower()
                if use in ['y', 'yes']:
                    player['position'] = ROOMS[dest]
                    player['in_room'] = dest
                    print(f"\nYou traveled to {dest} via secret passage!")
                    print("You MUST make a suggestion!")
                    suggestion_made = True
                    self.handle_room_entry(player, dest)
                    # After suggestion, turn ends (only 1 suggestion per turn)
                    return
        
        input(f"\nPress Enter to roll dice...")
        roll = random.randint(1, 6)
        print(f"\nYou rolled: {roll}")
        
        # If still in room (not already exited above when dragged), exit it now
        if player['in_room']:
            print(f"You must exit {player['in_room']} and move.")
            player['in_room'] = None
            player['was_dragged'] = False
        # Get all moves at once
        show_board(self.players)
        print(f"\nYou rolled: {roll}")
        print(f"Current position: {player['position']}")
        valid = self.get_valid_moves(player)
        print("Valid moves:", ", ".join(valid))
        
        # Collect all moves
        all_moves = []
        moves_entered = 0
        while moves_entered < roll:
            cmd = input(f"\nEnter move(s) ({roll - moves_entered} remaining, or 'DONE'): ").strip()
            if cmd.upper() == "DONE":
                break
            moves_list = cmd.upper().split()
            remaining = roll - moves_entered
            if len(moves_list) > remaining:
                print(f"You entered {len(moves_list)} moves but only have {remaining} remaining!")
                print(f"Using first {remaining} move(s)")
                moves_list = moves_list[:remaining]
            all_moves.extend(moves_list)
            moves_entered += len(moves_list)
            if moves_entered >= roll:
                break
        
        # Execute all moves silently, then show final position
        start_pos = player['position']
        moves_made = 0
        for d in all_moves:
            if moves_made >= roll:
                break
            if self.move_player(player, d):
                moves_made += 1
                # Check if entered room or center
                nr, nc = player['position']
                room = self.get_room_at(nr, nc)
                if room:
                    print(f"\nYou moved {moves_made} space(s) and entered {room}!")
                    if not suggestion_made:
                        self.handle_room_entry(player, room)  # MUST suggest (only 1 per turn)
                    return
                elif (nr, nc) == ACCUSATION_SPOT:
                    # Just continue - accusations can be made at any time
                    pass
            else:
                print(f"\nInvalid move '{d}' - stopping movement.")
                break
        
        # Show final position if didn't enter room
        if moves_made > 0:
            final_pos = player['position']
            if final_pos != start_pos:
                print(f"\nYou moved {moves_made} space(s). Final position: {final_pos}")
            else:
                print(f"\nNo valid moves could be made. Remaining at {final_pos}")
        else:
            print(f"\nYou remain at {start_pos}.")
    
    def _play_ai_turn(self, player):
        """Handle AI player's turn automatically."""
        ai = self.ai_controller
        
        print("\n" + "=" * 60)
        colored_name_token = format_player_name(player['name'], player['number'], player.get('eliminated'))
        print(f"TURN: {colored_name_token} [AI]")
        print("=" * 60)
        show_board(self.players)
        
        r, c = player['position']
        if player['in_room']:
            print(f"\n[AI] Currently in: {player['in_room']}")
        else:
            print(f"\n[AI] Position: ({r}, {c}) - In hallway")
        
        print(f"\n[AI] {ai.knowledge.get_knowledge_summary()}")
        time.sleep(0.5)  # Brief pause for readability
        
        # Check if AI should accuse (knows the solution!) - Can accuse anytime!
        if ai.should_accuse() and not player['has_accused']:
            print("\n[AI] *** I'VE DEDUCED THE SOLUTION! Making accusation... ***")
            time.sleep(1)
            character, weapon, room = ai.get_accusation()
            player['has_accused'] = True
            if self.make_accusation(player, character, weapon, room):
                self.game_over = True
            return
        
        # Track if suggestion was made this turn (only 1 per turn)
        suggestion_made = False
        
        # If dragged to a room, OPTIONAL suggestion (AI will choose strategically)
        if player['in_room'] and player.get('was_dragged'):
            print("\n[AI] I was dragged here.")
            room = player['in_room']
            player['was_dragged'] = False
            # AI decides if it should suggest (strategic decision)
            # For now, AI will suggest if it's beneficial (you can make this smarter)
            c, w, r = ai.choose_suggestion(room)
            # AI suggests if it's strategic (here we always suggest, but you could add logic)
            print("[AI] I'll make a suggestion...")
            time.sleep(0.5)
            suggestion_made = True
            self.make_suggestion(player, c, w, room)
            ai.entered_room(room)
            # Exit room after suggestion to allow movement
            player['in_room'] = None
            # Continue to dice roll below (don't return)
        
        # If turn starts in a room, NO suggestion - must exit first
        if player['in_room']:
            print(f"\n[AI] Starting turn in {player['in_room']}")
            print("[AI] Cannot suggest when starting in a room - must exit first.")
            
            # Check secret passage (using secret passage counts as entering)
            if player['in_room'] in SECRET_PASSAGES:
                dest = SECRET_PASSAGES[player['in_room']]
                if ai.should_use_secret_passage(player['in_room'], dest):
                    print(f"\n[AI] Using secret passage to {dest}!")
                    time.sleep(0.5)
                    player['position'] = ROOMS[dest]
                    player['in_room'] = dest
                    print(f"\n[AI] Entering {dest} - must suggest...")
                    suggestion_made = True
                    c, w, room = ai.choose_suggestion(dest)
                    self.make_suggestion(player, c, w, room)
                    ai.entered_room(dest)
                    # After entering via secret passage, suggestion is mandatory and turn ends
                    return
            
            # Must exit room to move
            current_room = player['in_room']
            print(f"\n[AI] Exiting {current_room} to move...")
            player['in_room'] = None
            player['was_dragged'] = False
        
        # Roll dice and move
        print("\n[AI] Rolling dice...")
        time.sleep(0.3)
        roll = random.randint(1, 6)
        print(f"[AI] Rolled: {roll}")
        
        # Note: Room exit is handled above if AI was in a room and made a suggestion
        
        # Get occupied positions for pathfinding
        occupied = set()
        for p in self.players:
            if p != player and not p['eliminated']:
                pos = p['position']
                # Only hallway positions count as blocked
                if not self.get_room_at(*pos) and pos != ACCUSATION_SPOT:
                    occupied.add(pos)
        
        # AI chooses moves
        moves = ai.choose_moves(player['position'], roll, occupied)
        print(f"[AI] Planning path: {' '.join(moves) if moves else 'staying put'}")
        time.sleep(0.3)
        
        # Execute moves
        moves_made = 0
        for direction in moves:
            if self.move_player(player, direction):
                nr, nc = player['position']
                print(f"[AI] Moved {direction} to ({nr}, {nc})")
                moves_made += 1
                time.sleep(0.2)
                
                # Check if entered a room
                room = self.get_room_at(nr, nc)
                if room:
                    print(f"\n[AI] Entered {room}!")
                    player['in_room'] = room
                    ai.entered_room(room)
                    # Only make suggestion if we haven't made one this turn (1 per turn max)
                    if not suggestion_made:
                        print("[AI] Must make a suggestion...")
                        time.sleep(0.5)
                        c, w, r = ai.choose_suggestion(room)
                        self.make_suggestion(player, c, w, room)
                    return
                elif (nr, nc) == ACCUSATION_SPOT:
                    # Just continue - accusations can be made at any time
                    pass
        
        print(f"\n[AI] Ended turn in hallway at {player['position']}")

    def play(self):
        self.game_over = False
        print("\n\nStarting game!")
        show_board(self.players)
        input("\nPress Enter to begin...")
        turn = 0
        while not self.game_over and turn < 100:
            self.play_turn()
            self.current_player = (self.current_player + 1) % self.num_players
            turn += 1
        print("\n\nGame Over!")

