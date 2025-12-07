"""
AI Player for Cluedo
Makes strategic decisions for movement, suggestions, and accusations.
"""

import random
from collections import deque
from data import CHARACTERS, WEAPONS, ROOMS, ACCUSATION_SPOT
from ai_knowledge import KnowledgeBase


class AIPlayer:
    """
    AI-controlled player that makes decisions based on knowledge and deduction.
    
    Capabilities:
    - Strategic movement toward target rooms
    - Smart suggestions to gather information
    - Only accuses when solution is CERTAIN
    - Strategic card showing when refuting
    """
    
    def __init__(self, player_number: int, num_players: int, player_data: dict):
        self.player_number = player_number
        self.num_players = num_players
        self.player_data = player_data  # Reference to player dict in game
        
        # Initialize knowledge base
        self.knowledge = KnowledgeBase(player_number, num_players)
        
        # Rooms we've visited (for variety in suggestions)
        self.visited_rooms = set()
        
        # Target room for movement
        self.target_room = None
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    def receive_cards(self, cards: list):
        """Receive dealt cards at game start."""
        self.knowledge.add_own_cards(cards)
        print(f"  [AI] Received {len(cards)} cards, analyzing...")
    
    # =========================================================================
    # MOVEMENT DECISIONS
    # =========================================================================
    
    def choose_target_room(self) -> str:
        """
        Choose which room to head toward.
        
        Strategy:
        1. Prioritize rooms that could be the solution
        2. Prefer unvisited rooms
        3. Avoid rooms we've been to recently
        
        Note: AI accuses at start of turn when solution is known,
        so no need to go to any specific location.
        """
        # Get rooms that could be in solution
        possible = self.knowledge.get_possible_solutions()
        solution_rooms = possible['rooms']
        
        # Prefer solution rooms we haven't visited
        unvisited_solution = solution_rooms - self.visited_rooms
        if unvisited_solution:
            self.target_room = random.choice(list(unvisited_solution))
            return self.target_room
        
        # Otherwise any solution room
        if solution_rooms:
            self.target_room = random.choice(list(solution_rooms))
            return self.target_room
        
        # Fallback: any unvisited room
        all_rooms = set(ROOMS.keys())
        unvisited = all_rooms - self.visited_rooms
        if unvisited:
            self.target_room = random.choice(list(unvisited))
            return self.target_room
        
        # Last resort: random room
        self.target_room = random.choice(list(ROOMS.keys()))
        return self.target_room
    
    def get_path_to_target(self, current_pos: tuple, target_pos: tuple, 
                           occupied_positions: set) -> list:
        """
        BFS pathfinding to target position.
        Returns list of moves like ['D', 'D', 'R', 'R'].
        """
        if current_pos == target_pos:
            return []
        
        # BFS
        queue = deque([(current_pos, [])])
        visited = {current_pos}
        
        directions = [
            ('U', -1, 0),
            ('D', 1, 0),
            ('L', 0, -1),
            ('R', 0, 1)
        ]
        
        while queue:
            (r, c), path = queue.popleft()
            
            for move, dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                # Check bounds (9x9 grid)
                if not (0 <= nr < 11 and 0 <= nc < 11):
                    continue
                
                # Check if visited
                if (nr, nc) in visited:
                    continue
                
                # Check if occupied (hallway collision)
                # Allow rooms and center to have multiple players
                is_room = self._is_room_position(nr, nc)
                is_center = (nr, nc) == ACCUSATION_SPOT
                if not is_room and not is_center and (nr, nc) in occupied_positions:
                    continue
                
                new_path = path + [move]
                
                # Found target?
                if (nr, nc) == target_pos:
                    return new_path
                
                # Check if we reached a room on the way
                if is_room or is_center:
                    # If this is our target type, return
                    if is_center and target_pos == ACCUSATION_SPOT:
                        return new_path
                    room_at = self._get_room_at(nr, nc)
                    target_room = self._get_room_at(*target_pos) if target_pos != ACCUSATION_SPOT else None
                    if room_at and room_at == target_room:
                        return new_path
                
                visited.add((nr, nc))
                queue.append(((nr, nc), new_path))
        
        # No path found - return empty
        return []
    
    def _is_room_position(self, r: int, c: int) -> bool:
        """Check if position is a room."""
        return (r, c) in ROOMS.values()
    
    def _get_room_at(self, r: int, c: int) -> str:
        """Get room name at position, or None."""
        for room, pos in ROOMS.items():
            if pos == (r, c):
                return room
        return None
    
    def choose_moves(self, current_pos: tuple, dice_roll: int, 
                    occupied_positions: set) -> list:
        """
        Choose moves for this turn.
        
        Returns list of direction commands up to dice_roll length.
        """
        # Decide target
        target_room = self.choose_target_room()
        
        if target_room == "CENTER":
            target_pos = ACCUSATION_SPOT
        else:
            target_pos = ROOMS.get(target_room, current_pos)
        
        # Get path
        path = self.get_path_to_target(current_pos, target_pos, occupied_positions)
        
        if not path:
            # Can't reach target, try random valid moves
            return self._random_moves(current_pos, dice_roll, occupied_positions)
        
        # Return up to dice_roll moves
        return path[:dice_roll]
    
    def _random_moves(self, current_pos: tuple, dice_roll: int, 
                      occupied_positions: set) -> list:
        """Generate random valid moves as fallback."""
        moves = []
        r, c = current_pos
        
        for _ in range(dice_roll):
            valid = []
            for move, dr, dc in [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 11 and 0 <= nc < 11:
                    is_room = self._is_room_position(nr, nc)
                    is_center = (nr, nc) == ACCUSATION_SPOT
                    if is_room or is_center or (nr, nc) not in occupied_positions:
                        valid.append((move, nr, nc))
            
            if valid:
                move, r, c = random.choice(valid)
                moves.append(move)
                # Stop if we enter a room
                if self._is_room_position(r, c) or (r, c) == ACCUSATION_SPOT:
                    break
            else:
                break
        
        return moves
    
    # =========================================================================
    # SUGGESTION DECISIONS
    # =========================================================================
    
    def choose_suggestion(self, current_room: str) -> tuple:
        """
        Choose character and weapon for suggestion (room is current room).
        
        Strategy:
        1. Suggest cards we DON'T know about (to gather info)
        2. Prioritize cards that could be in solution
        3. Sometimes suggest cards we know others have (to eliminate for other players)
        """
        possible = self.knowledge.get_possible_solutions()
        
        # Characters we don't know the owner of
        unknown_chars = possible['characters'] - self.knowledge.my_cards
        # Weapons we don't know the owner of  
        unknown_weapons = possible['weapons'] - self.knowledge.my_cards
        
        # Pick character
        if unknown_chars:
            character = random.choice(list(unknown_chars))
        else:
            # Suggest any character we don't have
            other_chars = set(CHARACTERS) - self.knowledge.my_cards
            character = random.choice(list(other_chars)) if other_chars else random.choice(CHARACTERS)
        
        # Pick weapon
        if unknown_weapons:
            weapon = random.choice(list(unknown_weapons))
        else:
            other_weapons = set(WEAPONS) - self.knowledge.my_cards
            weapon = random.choice(list(other_weapons)) if other_weapons else random.choice(WEAPONS)
        
        return (character, weapon, current_room)
    
    # =========================================================================
    # ACCUSATION DECISIONS
    # =========================================================================
    
    def should_accuse(self) -> bool:
        """
        Decide if AI should make an accusation.
        
        ONLY accuse when solution is CERTAIN (one option in each category).
        """
        return self.knowledge.is_solution_known()
    
    def get_accusation(self) -> tuple:
        """
        Get the accusation (character, weapon, room).
        Only call if should_accuse() returns True.
        """
        return self.knowledge.get_solution()
    
    # =========================================================================
    # REFUTATION DECISIONS
    # =========================================================================
    
    def choose_card_to_show(self, suggestion: tuple, matching_cards: list) -> str:
        """
        Choose which card to show when refuting.
        
        Strategy:
        - Show card that reveals least information
        - Prefer showing cards we've already shown before
        - Prefer showing cards that are NOT in solution possibilities
        """
        if len(matching_cards) == 1:
            return matching_cards[0]
        
        character, weapon, room = suggestion
        possible = self.knowledge.get_possible_solutions()
        
        # Prefer cards NOT in possible solution (they give less info)
        non_solution = []
        for card in matching_cards:
            if card not in possible['characters'] and \
               card not in possible['weapons'] and \
               card not in possible['rooms']:
                non_solution.append(card)
        
        if non_solution:
            return random.choice(non_solution)
        
        # Otherwise random
        return random.choice(matching_cards)
    
    def get_matching_cards(self, character: str, weapon: str, room: str) -> list:
        """Get cards from AI's hand that match the suggestion."""
        suggestion_cards = {character, weapon, room}
        return [card for card in self.knowledge.my_cards if card in suggestion_cards]
    
    # =========================================================================
    # SECRET PASSAGE DECISIONS
    # =========================================================================
    
    def should_use_secret_passage(self, current_room: str, destination: str) -> bool:
        """
        Decide whether to use a secret passage.
        
        Use it if destination is a room we want to visit.
        """
        if self.knowledge.is_solution_known():
            # Need to get to center, not rooms
            return False
        
        possible = self.knowledge.get_possible_solutions()
        
        # Use if destination could be solution and we haven't been there
        if destination in possible['rooms'] and destination not in self.visited_rooms:
            return True
        
        # 50% chance otherwise
        return random.random() < 0.5
    
    # =========================================================================
    # KNOWLEDGE UPDATES
    # =========================================================================
    
    def observe_suggestion(self, suggester: int, character: str, weapon: str,
                           room: str, refuter: int, card_shown: str,
                           players_who_passed: list):
        """
        Update knowledge based on observing a suggestion.
        
        If AI was the suggester, card_shown is known.
        Otherwise, card_shown is None.
        """
        if suggester == self.player_number:
            # AI made this suggestion
            if refuter:
                self.knowledge.process_ai_suggestion_refuted(
                    character, weapon, room, refuter, card_shown, players_who_passed
                )
            else:
                self.knowledge.process_ai_suggestion_not_refuted(
                    character, weapon, room, players_who_passed
                )
        else:
            # Another player made this suggestion
            if refuter:
                # If card_shown is provided (for testing or if AI can see it somehow),
                # use it; otherwise card_shown will be None
                self.knowledge.process_other_suggestion_refuted(
                    suggester, character, weapon, room, refuter, card_shown, players_who_passed
                )
            else:
                self.knowledge.process_other_suggestion_not_refuted(
                    suggester, character, weapon, room, players_who_passed
                )
    
    def entered_room(self, room: str):
        """Record that AI entered a room."""
        self.visited_rooms.add(room)
    
    # =========================================================================
    # DEBUG
    # =========================================================================
    
    def print_status(self):
        """Print AI's current status."""
        print(f"\n[AI P{self.player_number}] Status:")
        print(f"  Target room: {self.target_room}")
        print(f"  Visited: {self.visited_rooms}")
        print(f"  {self.knowledge.get_knowledge_summary()}")
        if self.should_accuse():
            print(f"  *** READY TO ACCUSE: {self.get_accusation()} ***")


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING AI PLAYER")
    print("=" * 60)
    
    # Create AI player
    player_data = {
        'name': 'Miss Scarlett',
        'number': 1,
        'position': (4, 4),  # Center
        'cards': [],
        'eliminated': False,
        'in_room': None
    }
    
    ai = AIPlayer(player_number=1, num_players=3, player_data=player_data)
    
    # Deal cards
    print("\n1. Dealing cards to AI...")
    ai.receive_cards([
        ('character', 'Miss Scarlett'),
        ('weapon', 'Candlestick'),
        ('room', 'Kitchen'),
        ('room', 'Study')
    ])
    
    # Test target selection
    print("\n2. AI chooses target room...")
    target = ai.choose_target_room()
    print(f"   Target: {target}")
    
    # Test pathfinding
    print("\n3. AI plans path from center to Kitchen...")
    path = ai.get_path_to_target(
        current_pos=(4, 4),
        target_pos=ROOMS['Kitchen'],  # (8, 8)
        occupied_positions=set()
    )
    print(f"   Path: {path}")
    
    # Test suggestion choice
    print("\n4. AI chooses suggestion in Hall...")
    suggestion = ai.choose_suggestion('Hall')
    print(f"   Suggests: {suggestion}")
    
    # Simulate learning
    print("\n5. Simulating game - AI learns from suggestions...")
    
    # AI suggests, P2 shows Colonel Mustard
    ai.observe_suggestion(
        suggester=1,
        character='Colonel Mustard', weapon='Rope', room='Library',
        refuter=2, card_shown='Colonel Mustard',
        players_who_passed=[3]
    )
    print("   AI suggested, learned P2 has Colonel Mustard")
    
    # AI suggests, NO ONE refutes!
    ai.observe_suggestion(
        suggester=1,
        character='Mrs. White', weapon='Dagger', room='Hall',
        refuter=None, card_shown=None,
        players_who_passed=[2, 3]
    )
    print("   AI suggested, NO ONE refuted - very informative!")
    
    # Check if ready to accuse
    print(f"\n6. Ready to accuse? {ai.should_accuse()}")
    ai.print_status()
    
    # Test card showing
    print("\n7. AI must refute suggestion (Scarlett, Candlestick, Lounge)...")
    matching = ai.get_matching_cards('Miss Scarlett', 'Candlestick', 'Lounge')
    print(f"   Matching cards: {matching}")
    if matching:
        choice = ai.choose_card_to_show(('Miss Scarlett', 'Candlestick', 'Lounge'), matching)
        print(f"   AI chooses to show: {choice}")
    
    print("\n✓ AI Player test complete!")

