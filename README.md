# Cluedo Project

A Python implementation of the classic murder mystery board game Cluedo (also known as Clue) with **AI opponent support**.

## Installation

### Clone from GitHub

```bash
git clone https://github.com/aditn2003/Cluedo-Game-Project.git
cd Cluedo-Game-Project
```

### Requirements

- **Python 3.8+** (no external dependencies needed!)
- Works on Windows, macOS, and Linux

## Quick Start

```bash
python main.py
```

---

## About the Game

In Cluedo, players take on the roles of guests at a mansion where a murder has taken place. The goal is to determine three things:
- **Who** committed the murder (which character)
- **What** weapon was used
- **Where** the murder took place (which room)

## Game Features

| Feature | Description |
|---------|-------------|
| **2-6 Players** | Choose how many players at game start |
| **AI Opponent** | Optional intelligent AI player (P1) |
| **11x11 Grid Board** | Simple, easy-to-read console display |
| **Full Cluedo Rules** | Suggestions, refutations, accusations |
| **Secret Passages** | Shortcuts between corner rooms |
| **Deduction Helper** | Shows what cards you've seen |

---

## How to Play

### Game Setup
1. Run `python main.py`
2. Choose number of players (2-6)
3. Choose if Player 1 should be AI controlled
4. Cards are dealt, solution is sealed in envelope

### Your Turn
1. **Accusation?** - You can make ONE accusation per game (anytime!)
2. **In a room?** - Make an optional suggestion
3. **Secret passage?** - Use it to travel instantly (if available)
4. **Roll dice** - Get 1-6 moves
5. **Move** - Enter directions: `U` (up), `D` (down), `L` (left), `R` (right)
6. **Enter a room** → MUST make a suggestion

### Movement Commands
- Single move: `D` or `DOWN`
- Multiple moves: `D D R` or `DOWN DOWN RIGHT`
- End early: `DONE`

### Suggestions
When you enter a room, you MUST suggest:
- **Who** did it (pick a character)
- **What** weapon (pick a weapon)
- **Where** (automatically your current room)

Other players check their cards clockwise. First player with a matching card shows ONE card to you privately.

### Accusations
- Can be made once per game, anytime during your turn
- Guess the **character**, **weapon**, and **room**
- **Correct** = YOU WIN!!!
- **Wrong** = You're eliminated (but can still refute)

---

## The AI Player

The AI uses logical deduction with a knowledge base:

| Capability | How It Works |
|------------|--------------|
| **Card Tracking** | Remembers all cards it's seen |
| **Elimination** | Removes known cards from solution candidates |
| **Inference** | Deduces from "no refute" scenarios |
| **Strategic Suggestions** | Asks about unknown cards |
| **Smart Refutation** | Shows least valuable card |
| **Certain Accusations** | Only accuses when 100% sure |

---

## Board Layout (11x11)

```
     0  1  2  3  4  5  6  7  8  9 10
    ---------------------------------
 0 | S  .  .  .  .  H  .  .  .  .  L
 1 | .  .  .  .  .  .  .  .  .  .  .
 2 | .  .  .  .  .  .  .  .  .  .  .
 3 | .  .  .  .  .  .  .  .  .  .  .
 4 | l  .  .  .  .  B  .  .  .  .  D
 5 | .  .  .  .  .  .  .  .  .  .  .
 6 | .  .  .  .  .  .  .  .  .  .  .
 7 | .  .  .  .  .  .  .  .  .  .  .
 8 | .  .  .  .  .  .  .  .  .  .  .
 9 | .  .  .  .  .  .  .  .  .  .  .
10 | C  .  .  .  .  b  .  .  .  .  K
```

**Room Legend:**
| Symbol | Room |
|--------|------|
| `S` | Study |
| `H` | Hall |
| `L` | Lounge |
| `l` | Library |
| `B` | Billiard |
| `D` | Dining |
| `C` | Conservatory |
| `b` | Ballroom |
| `K` | Kitchen |
| `.` | Hallway |
| `P1`-`P6` | Players |

## Secret Passages

Corner rooms have secret passages for instant travel:
- **Study** ↔ **Kitchen** (diagonal corners)
- **Conservatory** ↔ **Lounge** (diagonal corners)

---

## Rules Summary

| Action | When | Required? |
|--------|------|-----------|
| Suggestion | Enter a room | YES - mandatory |
| Suggestion | Start turn in room | NO - optional |
| Suggestion | Dragged to room | NO - optional |
| Accusation | Anytime during turn | ONE per game |

---

## Game Components

### Characters (6)
Miss Scarlett, Colonel Mustard, Mrs. White, Reverend Green, Mrs. Peacock, Professor Plum

### Weapons (6)
Candlestick, Dagger, Lead Pipe, Revolver, Rope, Wrench

### Rooms (9)
Study, Hall, Lounge, Library, Billiard, Dining, Conservatory, Ballroom, Kitchen

---

## Project Structure

```
Cluedo-Game-Project/
├── main.py           # Entry point - run this to play!
├── cluedo.py         # Main game class and game loop
├── data.py           # Game constants (characters, weapons, rooms)
├── board.py          # Board display and rendering
├── ai_player.py      # AI player decision making
├── ai_knowledge.py   # AI knowledge base and deduction engine
└── README.md         # This file
```

### Module Descriptions

| File | Purpose | Lines |
|------|---------|-------|
| `main.py` | Entry point, starts game |
| `cluedo.py` | Game logic, turn handling, suggestions |
| `data.py` | Constants: characters, weapons, rooms |
| `board.py` | Console board display |
| `ai_player.py` | AI decision making | 
| `ai_knowledge.py` | AI knowledge tracking & deduction |

---

## Technical Details

- **Language:** Python 3.8+
- **Dependencies:** None (standard library only)
- **Platform:** Cross-platform (Windows, macOS, Linux)
- **Interface:** Console/Terminal

### AI Implementation
- Knowledge representation using Python sets and dicts
- Constraint satisfaction for "at least one" deductions
- BFS pathfinding for movement
- Iterative deduction engine

---

## Educational Value

This project demonstrates:
- Object-oriented programming in Python
- Game state management
- AI concepts (knowledge representation, logical inference)
- Clean code organization and documentation

---

## License

This is an educational project implementing the classic board game Cluedo.

---

## Links

- **Repository:** https://github.com/aditn2003/Cluedo-Game-Project
- **Author:** aditn2003


