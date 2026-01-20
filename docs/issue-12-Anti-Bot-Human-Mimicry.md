# issue 12: Anti-Bot Human Mimicry

## Overview
This task implements human-like behavior in the LinkedIn Scraper to **avoid LinkedIn bot detection**. The scraper simulates natural browsing patterns such as mouse movements, typing, scrolling, and idle presence, making automated scraping more human-like.

---

## Implemented Features

### 1. Real Human Mouse Movement
**Method:** `_human_mouse_movement(moves=5)`  
- Performs small random left/right/up/down movements of the mouse.  
- Used during login, typing, and interaction with elements.  
- Randomized offsets and pause durations mimic natural hand movements.

---

### 2. Random Harmless Actions
**Method:** `_random_human_action()`  
- Randomly performs one of the following actions:
  - Small mouse movements
  - Tiny scrolls up or down
  - Short idle pauses
- Adds unpredictability to user behavior, reducing bot detection.

---

### 3. Human-Like Typing
**Method:** `_human_typing(element, text)`  
- Types text character by character with **variable delays** between keystrokes.  
- Includes a short pause after finishing typing.  
- Use
