#!/usr/bin/env python3
"""
Cluedo Game - Entry Point

A digital implementation of the classic murder mystery board game.
Run this file to start the game.

Usage:
    python main.py              # Normal play
    python main.py --debug      # Show solution at start (for testing)
    python main.py -d           # Short form

Repository: https://github.com/aditn2003/Cluedo-Game-Project
"""
import sys
from cluedo import SimpleCluedo

def main():
    # Check for debug flag
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    
    print("\n" + "="*60)
    print("SIMPLE CLUEDO")
    print("="*60)
    
    if debug_mode:
        print("\n[DEBUG MODE ENABLED]")
        print("The solution will be shown at game start.")
        print("="*60)
    
    print("\nFeatures:")
    print("  • 11x11 grid with all 9 rooms")
    print("  • 2-6 players (you choose)")
    print("  • Optional AI opponent (P1)")
    print("  • Simple display with P1-P6 and room letters")
    print("  • Easy to understand!")
    print("="*60)
    
    input("\nPress Enter to start...")
    game = SimpleCluedo(debug=debug_mode)
    game.play()

if __name__ == "__main__":
    main()
