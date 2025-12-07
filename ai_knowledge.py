"""
AI Knowledge Base for Cluedo
Tracks what the AI knows about cards, players, and possible solutions.
"""

from data import CHARACTERS, WEAPONS, ROOMS


class KnowledgeBase:
    """
    Maintains the AI's knowledge about the game state.
    
    Tracks:
    - Cards the AI owns
    - Cards each player definitely has
    - Cards each player definitely doesn't have  
    - Possible solutions (not yet eliminated)
    - Suggestion history for inference
    """
    
    def __init__(self, ai_player_number: int, num_players: int):
        self.ai_player_number = ai_player_number
        self.num_players = num_players
        
        # Cards the AI owns (from dealt hand)
        self.my_cards = set()
        
        # For each player, track cards they definitely HAVE
        # player_has[player_num] = set of cards
        self.player_has = {i: set() for i in range(1, num_players + 1)}
        
        # For each player, track cards they definitely DON'T have
        # player_lacks[player_num] = set of cards  
        self.player_lacks = {i: set() for i in range(1, num_players + 1)}
        
        # Possible solution candidates (start with all, eliminate as we learn)
        self.possible_characters = set(CHARACTERS)
        self.possible_weapons = set(WEAPONS)
        self.possible_rooms = set(ROOMS.keys())
        
        # History of suggestions for complex inference
        # Each entry: {
        #   'suggester': player_num,
        #   'character': str,
        #   'weapon': str, 
        #   'room': str,
        #   'refuter': player_num or None,
        #   'card_shown': str or None (only if AI was suggester)
        #   'players_who_passed': [player_nums who couldn't refute]
        # }
        self.suggestion_history = []
        
        # Constraints: "player X has at least one of [card1, card2, card3]"
        # Used for advanced inference
        self.at_least_one_constraints = []  # [(player_num, set of cards)]
    
    # =========================================================================
    # CARD TRACKING METHODS
    # =========================================================================
    
    def add_own_card(self, card: str):
        """Add a card to AI's own hand."""
        self.my_cards.add(card)
        self.player_has[self.ai_player_number].add(card)
        # If AI has it, eliminate from solution
        self._eliminate_from_solution(card)
    
    def add_own_cards(self, cards: list):
        """Add multiple cards to AI's hand (from initial deal)."""
        for card_type, card_name in cards:
            self.add_own_card(card_name)
    
    def mark_player_has_card(self, player_num: int, card: str):
        """Mark that a specific player definitely has a card."""
        # Safety check: Only mark if we're actually certain
        # (Don't eliminate solution candidates unless we're sure)
        self.player_has[player_num].add(card)
        # If anyone has it, it's not the solution
        # This is safe because we only call this when we KNOW a player has the card
        self._eliminate_from_solution(card)
        # Remove from "lacks" if it was there
        self.player_lacks[player_num].discard(card)
    
    def mark_player_lacks_card(self, player_num: int, card: str):
        """Mark that a specific player definitely doesn't have a card."""
        if card not in self.player_has[player_num]:
            self.player_lacks[player_num].add(card)
    
    def mark_player_lacks_cards(self, player_num: int, cards: list):
        """Mark that a player doesn't have any of these cards."""
        for card in cards:
            self.mark_player_lacks_card(player_num, card)
    
    # =========================================================================
    # SOLUTION TRACKING
    # =========================================================================
    
    def _eliminate_from_solution(self, card: str):
        """Remove a card from possible solutions (it's been seen)."""
        # Remove from the correct category only - a card can only be in one category
        if card in CHARACTERS:
            self.possible_characters.discard(card)
        elif card in WEAPONS:
            self.possible_weapons.discard(card)
        elif card in ROOMS:
            self.possible_rooms.discard(card)
    
    def get_possible_solutions(self) -> dict:
        """Get current possible solution candidates."""
        return {
            'characters': self.possible_characters.copy(),
            'weapons': self.possible_weapons.copy(),
            'rooms': self.possible_rooms.copy()
        }
    
    def is_solution_known(self) -> bool:
        """Check if we've narrowed down to exactly one solution."""
        return (len(self.possible_characters) == 1 and 
                len(self.possible_weapons) == 1 and 
                len(self.possible_rooms) == 1)
    
    def get_solution(self) -> tuple:
        """Get the deduced solution (only call if is_solution_known() is True)."""
        if not self.is_solution_known():
            return None
        return (
            list(self.possible_characters)[0],
            list(self.possible_weapons)[0],
            list(self.possible_rooms)[0]
        )
    
    # =========================================================================
    # SUGGESTION HISTORY
    # =========================================================================
    
    def record_suggestion(self, suggester: int, character: str, weapon: str, 
                         room: str, refuter: int = None, card_shown: str = None,
                         players_who_passed: list = None):
        """
        Record a suggestion and what happened.
        
        Args:
            suggester: Player number who made suggestion
            character, weapon, room: The suggestion
            refuter: Player who showed a card (None if no one could)
            card_shown: The card shown (only known if AI was suggester)
            players_who_passed: List of players who couldn't refute
        """
        self.suggestion_history.append({
            'suggester': suggester,
            'character': character,
            'weapon': weapon,
            'room': room,
            'refuter': refuter,
            'card_shown': card_shown,
            'players_who_passed': players_who_passed or []
        })
    
    def add_constraint(self, player_num: int, possible_cards: set):
        """
        Add constraint: player has at least one of these cards.
        Used when someone refutes but we don't know which card.
        """
        # Don't add if we already know they have one of these
        known_overlap = self.player_has[player_num] & possible_cards
        if known_overlap:
            return  # Already satisfied
        
        self.at_least_one_constraints.append((player_num, possible_cards.copy()))
    
    # =========================================================================
    # DEDUCTION ENGINE - Phase 2
    # =========================================================================
    
    def process_ai_suggestion_refuted(self, character: str, weapon: str, room: str,
                                       refuter: int, card_shown: str, 
                                       players_who_passed: list):
        """
        Process when AI made a suggestion and someone refuted by showing a card.
        
        AI knows EXACTLY which card was shown.
        Players who passed definitely lack all 3 cards.
        """
        suggestion_cards = {character, weapon, room}
        
        # Record the suggestion
        self.record_suggestion(
            suggester=self.ai_player_number,
            character=character, weapon=weapon, room=room,
            refuter=refuter, card_shown=card_shown,
            players_who_passed=players_who_passed
        )
        
        # AI saw the card - we know refuter has it
        self.mark_player_has_card(refuter, card_shown)
        
        # All players who passed lack ALL THREE cards
        for player in players_who_passed:
            self.mark_player_lacks_cards(player, list(suggestion_cards))
        
        # Run full deduction
        self.run_deduction()
    
    def process_ai_suggestion_not_refuted(self, character: str, weapon: str, room: str,
                                          players_checked: list):
        """
        Process when AI made a suggestion and NO ONE could refute.
        
        This is VERY powerful - all other players lack all 3 cards!
        Since AI doesn't have any of them (AI wouldn't suggest its own cards),
        these cards MUST be the solution!
        """
        suggestion_cards = {character, weapon, room}
        
        # Record the suggestion
        self.record_suggestion(
            suggester=self.ai_player_number,
            character=character, weapon=weapon, room=room,
            refuter=None, card_shown=None,
            players_who_passed=players_checked
        )
        
        # ALL players checked lack ALL THREE cards
        for player in players_checked:
            self.mark_player_lacks_cards(player, list(suggestion_cards))
        
        # CRITICAL INFERENCE: If AI suggested these and no one refuted,
        # and AI doesn't have any of them (AI wouldn't suggest its own cards),
        # then these three cards MUST be the solution!
        ai_has_any = bool(suggestion_cards & self.my_cards)
        
        if not ai_has_any:
            # AI doesn't have any of these cards, and no one else does either
            # This means these three cards ARE the solution!
            self.possible_characters = {character}
            self.possible_weapons = {weapon}
            self.possible_rooms = {room}
            # Eliminate all other cards from solution
            for char in CHARACTERS:
                if char != character:
                    self._eliminate_from_solution(char)
            for weap in WEAPONS:
                if weap != weapon:
                    self._eliminate_from_solution(weap)
            for rm in ROOMS.keys():
                if rm != room:
                    self._eliminate_from_solution(rm)
        
        # Run full deduction (even though we already narrowed it down)
        self.run_deduction()
    
    def process_other_suggestion_refuted(self, suggester: int, character: str, 
                                          weapon: str, room: str, refuter: int,
                                          card_shown: str = None,
                                          players_who_passed: list = None):
        """
        Process when another player made a suggestion and someone refuted.
        
        If card_shown is provided (for testing or if known), AI knows exactly which card.
        Otherwise, AI only knows:
        - Refuter has AT LEAST ONE of the 3 cards
        - Players who passed lack ALL THREE cards
        """
        if players_who_passed is None:
            players_who_passed = []
            
        suggestion_cards = {character, weapon, room}
        
        # Record the suggestion
        self.record_suggestion(
            suggester=suggester,
            character=character, weapon=weapon, room=room,
            refuter=refuter, card_shown=card_shown,  # May be None if AI doesn't see it
            players_who_passed=players_who_passed
        )
        
        # If AI knows which card was shown, mark that the refuter has it
        if card_shown:
            self.mark_player_has_card(refuter, card_shown)
        
        # Players who passed lack all three
        for player in players_who_passed:
            if player != self.ai_player_number:  # AI knows own cards
                self.mark_player_lacks_cards(player, list(suggestion_cards))
        
        # If we don't know which card, refuter has at least one (add constraint)
        if not card_shown:
            self.add_constraint(refuter, suggestion_cards)
        
        # Run full deduction
        self.run_deduction()
    
    def process_other_suggestion_not_refuted(self, suggester: int, character: str,
                                              weapon: str, room: str,
                                              players_checked: list):
        """
        Process when another player's suggestion wasn't refuted by anyone.
        
        All players checked (except suggester) lack all 3 cards.
        If we can verify the suggester doesn't have them either,
        then these cards MUST be the solution!
        """
        suggestion_cards = {character, weapon, room}
        
        # Record the suggestion
        self.record_suggestion(
            suggester=suggester,
            character=character, weapon=weapon, room=room,
            refuter=None, card_shown=None,
            players_who_passed=players_checked
        )
        
        # All checked players lack all three
        for player in players_checked:
            if player != self.ai_player_number:
                self.mark_player_lacks_cards(player, list(suggestion_cards))
        
        # CRITICAL INFERENCE: If no one could refute and we know:
        # 1. All checked players lack all three cards
        # 2. AI doesn't have any of them (or we'd know)
        # 3. The suggester also doesn't have any of them (we know from previous deductions)
        # Then these three cards MUST be the solution!
        
        ai_has_any = bool(suggestion_cards & self.my_cards)
        suggester_has_any = bool(suggestion_cards & self.player_has.get(suggester, set()))
        suggester_known_lacks = suggestion_cards & self.player_lacks.get(suggester, set())
        
        # If suggester is known to lack all three, and AI doesn't have any, it's the solution!
        if not ai_has_any and len(suggester_known_lacks) == 3:
            # All three cards are in solution!
            self.possible_characters = {character}
            self.possible_weapons = {weapon}
            self.possible_rooms = {room}
            # Eliminate all other cards from solution
            for char in CHARACTERS:
                if char != character:
                    self._eliminate_from_solution(char)
            for weap in WEAPONS:
                if weap != weapon:
                    self._eliminate_from_solution(weap)
            for rm in ROOMS.keys():
                if rm != room:
                    self._eliminate_from_solution(rm)
        # If we don't know about suggester yet, we'll learn more through deduction
        
        # Run full deduction
        self.run_deduction()
    
    def run_deduction(self):
        """
        Main deduction engine - applies all inference rules iteratively
        until no new information is gained.
        """
        changed = True
        iterations = 0
        max_iterations = 20  # Prevent infinite loops
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            # 1. Check if we can infer solution from "no refute" suggestions
            if self._infer_solution_from_no_refutes():
                changed = True
            
            # 2. Process "at least one" constraints
            if self._resolve_constraints():
                changed = True
            
            # 3. If only one player can have a card, they must have it
            if self._infer_unique_holder():
                changed = True
            
            # 4. Check if solution categories are narrowed to one
            # (This happens automatically via elimination)
    
    def _infer_solution_from_no_refutes(self) -> bool:
        """
        Check suggestion history for cases where no one refuted.
        
        If a suggestion had no refuter and we can verify that:
        - AI doesn't have any of the three cards
        - All other players don't have any of the three cards
        Then those three cards MUST be the solution!
        
        Returns True if solution was inferred.
        """
        changed = False
        
        for suggestion in self.suggestion_history:
            if suggestion['refuter'] is not None:
                continue  # Someone refuted, skip
            
            character = suggestion['character']
            weapon = suggestion['weapon']
            room = suggestion['room']
            suggester = suggestion['suggester']
            suggestion_cards = {character, weapon, room}
            
            # Check if AI has any of these cards
            ai_has_any = bool(suggestion_cards & self.my_cards)
            if ai_has_any:
                continue  # AI has one, can't be solution
            
            # For AI's own suggestions: if no one refuted, it MUST be the solution
            if suggester == self.ai_player_number:
                # AI suggested these and no one refuted
                # Since AI doesn't have them, they must be the solution
                if (self.possible_characters != {character} or
                    self.possible_weapons != {weapon} or
                    self.possible_rooms != {room}):
                    self.possible_characters = {character}
                    self.possible_weapons = {weapon}
                    self.possible_rooms = {room}
                    # Eliminate all others
                    for char in CHARACTERS:
                        if char != character:
                            self._eliminate_from_solution(char)
                    for weap in WEAPONS:
                        if weap != weapon:
                            self._eliminate_from_solution(weap)
                    for rm in ROOMS.keys():
                        if rm != room:
                            self._eliminate_from_solution(rm)
                    changed = True
                    continue
            
            # For other players' suggestions: check if we know suggester doesn't have them
            suggester_has = suggestion_cards & self.player_has.get(suggester, set())
            suggester_lacks_all = len(suggestion_cards & self.player_lacks.get(suggester, set())) == 3
            
            if suggester_lacks_all and not suggester_has:
                # Suggester doesn't have any, AI doesn't have any, no one else refuted
                # Must be the solution!
                if (self.possible_characters != {character} or
                    self.possible_weapons != {weapon} or
                    self.possible_rooms != {room}):
                    self.possible_characters = {character}
                    self.possible_weapons = {weapon}
                    self.possible_rooms = {room}
                    # Eliminate all others
                    for char in CHARACTERS:
                        if char != character:
                            self._eliminate_from_solution(char)
                    for weap in WEAPONS:
                        if weap != weapon:
                            self._eliminate_from_solution(weap)
                    for rm in ROOMS.keys():
                        if rm != room:
                            self._eliminate_from_solution(rm)
                    changed = True
        
        return changed
    
    def _resolve_constraints(self) -> bool:
        """
        Try to resolve "player has at least one of [cards]" constraints.
        
        If player is known to lack all but one card in the set,
        they MUST have that remaining card.
        
        CRITICAL: We can ONLY infer a player has a card if it's NOT a solution candidate.
        Solution candidates are cards that no one is known to have.
        
        Returns True if any new info was learned.
        """
        changed = False
        remaining_constraints = []
        
        # Get all solution candidates (cards that could be in the solution)
        solution_candidates = self.possible_characters | self.possible_weapons | self.possible_rooms
        
        for player_num, possible_cards in self.at_least_one_constraints:
            # Remove cards we now know this player lacks
            still_possible = possible_cards - self.player_lacks[player_num]
            
            # Remove cards we know someone else has (including AI)
            for other_player, their_cards in self.player_has.items():
                if other_player != player_num:
                    still_possible -= their_cards
            
            # CRITICAL: Do NOT resolve if the remaining card is a solution candidate
            # Only resolve if we have a non-solution card left
            non_solution_cards = still_possible - solution_candidates
            
            if len(non_solution_cards) == 0:
                # All remaining cards are solution candidates - can't resolve yet
                # Keep the constraint for later
                if len(still_possible) > 0:
                    remaining_constraints.append((player_num, still_possible))
                continue
            elif len(non_solution_cards) == 1:
                # Player MUST have this card (and it's not a solution candidate)
                card = list(non_solution_cards)[0]
                if card not in self.player_has[player_num]:
                    self.mark_player_has_card(player_num, card)
                    changed = True
            else:
                # Can't resolve yet (multiple non-solution cards or mixed with solution)
                remaining_constraints.append((player_num, still_possible))
        
        self.at_least_one_constraints = remaining_constraints
        return changed
    
    def _infer_unique_holder(self) -> bool:
        """
        If all players except one are known to lack a card,
        and we don't have it, that player must have it.
        
        IMPORTANT: If AI doesn't have a card and all other players lack it,
        the card MUST be in the solution - do NOT eliminate it!
        
        Returns True if any new info was learned.
        """
        changed = False
        all_cards = set(CHARACTERS) | set(WEAPONS) | set(ROOMS.keys())
        
        for card in all_cards:
            # Skip if we already know who has it
            found_holder = False
            for player_cards in self.player_has.values():
                if card in player_cards:
                    found_holder = True
                    break
            if found_holder:
                continue
            
            # Check if AI has this card (if so, it's already eliminated from solution)
            ai_has_card = card in self.my_cards
            
            # Find players who COULD have this card (don't check AI since we handle it separately)
            possible_holders = []
            for player_num in range(1, self.num_players + 1):
                if player_num == self.ai_player_number:
                    # For AI, check if it has the card (already eliminated from solution if so)
                    continue
                if card not in self.player_lacks[player_num]:
                    possible_holders.append(player_num)
            
            # If AI has it, it's already eliminated - skip
            if ai_has_card:
                continue
            
            # Check if card is a solution candidate
            is_solution_candidate = (card in self.possible_characters or 
                                   card in self.possible_weapons or 
                                   card in self.possible_rooms)
            
            # If only one OTHER player can have it
            if len(possible_holders) == 1:
                holder = possible_holders[0]
                # CRITICAL: Only infer they have it if it's NOT a solution candidate
                # If it's a solution candidate, it might actually be in the solution
                if not is_solution_candidate:
                    self.mark_player_has_card(holder, card)
                    changed = True
            elif len(possible_holders) == 0:
                # All other players lack it AND AI doesn't have it
                # This means it MUST be in the solution!
                # DO NOT eliminate it - ensure it stays in possible_* sets
                # (It should already be there, just make sure we don't remove it)
                if not is_solution_candidate:
                    # This shouldn't happen - if no one can have it and AI doesn't have it,
                    # it must be in solution. But if it's not in solution sets, something's wrong.
                    pass
        
        return changed
    
    def get_cards_that_could_be_solution(self) -> dict:
        """
        Get cards that could be in the solution.
        A card could be solution if NO player is known to have it.
        """
        all_known = set()
        for player_cards in self.player_has.values():
            all_known |= player_cards
        
        return {
            'characters': self.possible_characters - all_known,
            'weapons': self.possible_weapons - all_known,
            'rooms': self.possible_rooms - all_known
        }
    
    # =========================================================================
    # KNOWLEDGE QUERIES
    # =========================================================================
    
    def get_unknown_cards(self) -> set:
        """Get all cards we haven't identified the owner of yet."""
        all_cards = set(CHARACTERS) | set(WEAPONS) | set(ROOMS.keys())
        known = set()
        for player_cards in self.player_has.values():
            known |= player_cards
        return all_cards - known
    
    def get_player_possible_cards(self, player_num: int) -> set:
        """Get cards a player might have (not known to lack)."""
        all_cards = set(CHARACTERS) | set(WEAPONS) | set(ROOMS.keys())
        return all_cards - self.player_lacks[player_num] - self.my_cards
    
    def could_be_solution(self, character: str, weapon: str, room: str) -> bool:
        """Check if a given combination could still be the solution."""
        return (character in self.possible_characters and
                weapon in self.possible_weapons and
                room in self.possible_rooms)
    
    # =========================================================================
    # DEBUG / DISPLAY
    # =========================================================================
    
    def print_knowledge(self):
        """Print current knowledge state (for debugging)."""
        print("\n" + "=" * 50)
        print(f"AI (P{self.ai_player_number}) KNOWLEDGE BASE")
        print("=" * 50)
        
        print(f"\nMy cards: {self.my_cards}")
        
        print(f"\nPossible solutions:")
        print(f"  Characters: {self.possible_characters}")
        print(f"  Weapons: {self.possible_weapons}")
        print(f"  Rooms: {self.possible_rooms}")
        
        if self.is_solution_known():
            print(f"\n*** SOLUTION DEDUCED: {self.get_solution()} ***")
        
        print(f"\nKnown player cards:")
        for p, cards in self.player_has.items():
            if cards and p != self.ai_player_number:
                print(f"  P{p} has: {cards}")
        
        print(f"\nPlayers definitely lack:")
        for p, cards in self.player_lacks.items():
            if cards:
                print(f"  P{p} lacks: {cards}")
        
        print("=" * 50)
    
    def get_knowledge_summary(self) -> str:
        """Get a brief summary of current knowledge."""
        poss = self.get_possible_solutions()
        return (f"Possible: {len(poss['characters'])} chars, "
                f"{len(poss['weapons'])} weapons, {len(poss['rooms'])} rooms")


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING AI KNOWLEDGE BASE & DEDUCTION ENGINE")
    print("=" * 60)
    
    # Create AI as Player 1 in a 3-player game
    kb = KnowledgeBase(ai_player_number=1, num_players=3)
    
    # AI gets dealt some cards
    print("\n1. AI dealt cards: Miss Scarlett, Candlestick, Kitchen, Study")
    kb.add_own_cards([
        ('character', 'Miss Scarlett'),
        ('weapon', 'Candlestick'),
        ('room', 'Kitchen'),
        ('room', 'Study')
    ])
    
    print(f"   {kb.get_knowledge_summary()}")
    
    # AI makes a suggestion and P2 shows Colonel Mustard
    print("\n2. AI suggests: Colonel Mustard, Rope, Library")
    print("   P2 shows: Colonel Mustard (P3 couldn't refute)")
    kb.process_ai_suggestion_refuted(
        character='Colonel Mustard',
        weapon='Rope', 
        room='Library',
        refuter=2,
        card_shown='Colonel Mustard',
        players_who_passed=[3]  # P3 couldn't refute
    )
    
    print(f"   → P2 has: {kb.player_has[2]}")
    print(f"   → P3 lacks: {kb.player_lacks[3]}")
    print(f"   {kb.get_knowledge_summary()}")
    
    # AI makes another suggestion - NO ONE can refute!
    print("\n3. AI suggests: Mrs. White, Dagger, Hall")
    print("   NO ONE can refute! (P2, P3 both passed)")
    kb.process_ai_suggestion_not_refuted(
        character='Mrs. White',
        weapon='Dagger',
        room='Hall',
        players_checked=[2, 3]
    )
    
    print(f"   → P2 lacks: {kb.player_lacks[2]}")
    print(f"   → P3 lacks: {kb.player_lacks[3]}")
    print(f"   {kb.get_knowledge_summary()}")
    
    # P2 makes a suggestion, P3 refutes (AI doesn't see card)
    print("\n4. P2 suggests: Professor Plum, Wrench, Lounge")
    print("   P3 refutes (AI doesn't see which card)")
    kb.process_other_suggestion_refuted(
        suggester=2,
        character='Professor Plum',
        weapon='Wrench',
        room='Lounge',
        refuter=3,
        players_who_passed=[]  # No one passed before P3
    )
    
    print(f"   → Constraint: P3 has at least one of {{Plum, Wrench, Lounge}}")
    print(f"   {kb.get_knowledge_summary()}")
    
    # Show final knowledge state
    kb.print_knowledge()
    
    # Show what could be solution
    print("\nCards that could be the SOLUTION:")
    solution_candidates = kb.get_cards_that_could_be_solution()
    print(f"  Characters: {solution_candidates['characters']}")
    print(f"  Weapons: {solution_candidates['weapons']}")
    print(f"  Rooms: {solution_candidates['rooms']}")
    
    print("\n✓ Deduction Engine test complete!")
    print(f"  Solution known? {kb.is_solution_known()}")

