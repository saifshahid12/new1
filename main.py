import sys
import os
import tkinter as tk
from gui_app import LinkedInScraperGUI

def main():
    # Check if gui_app.py exists (Optional but good for safety)
    if not os.path.exists("gui_app.py"):
        print("Error: gui_app.py not found!")
        return

    # Initialize Tkinter and Start the App
    root = tk.Tk()
    app = LinkedInScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Application failed to start: {e}")
        input("Press Enter to exit...") 