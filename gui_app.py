import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
from datetime import datetime
from src.scraper import LinkedInScraper
from src.utils import load_config, export_data, extract_emails_from_text

import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


CONFIG_PATH = resource_path(os.path.join("config", "config.json"))

class LinkedInScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔗 LinkedIn Lead Scraper Control Panel")
        self.root.geometry("1150x900")
        
        try:
            self.config = load_config(CONFIG_PATH)
        except Exception:
            messagebox.showerror("Error", "Config file not found.")
            self.root.destroy()
            return

        self.setup_ui()

    def setup_ui(self):
        sidebar = tk.Frame(self.root, width=250, bg="#262730", padx=10, pady=10)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="⚙️ Execution", font=("Arial", 12, "bold"), bg="#262730", fg="white").pack(pady=10)
        self.run_btn = tk.Button(sidebar, text="🚀 Start Scraping", bg="#FF4B4B", fg="white", 
                                 font=("Arial", 10, "bold"), command=self.start_scraping_thread, height=2)
        self.run_btn.pack(fill="x", pady=10)

        self.log_area = scrolledtext.ScrolledText(sidebar, width=30, height=30, font=("Consolas", 8), bg="#1e1e1e", fg="#00ff00")
        self.log_area.pack(fill="both", expand=True, pady=5)

        main_frame = tk.Frame(self.root, padx=20, pady=10)
        main_frame.pack(side="right", fill="both", expand=True)

        self.tab_control = ttk.Notebook(main_frame)
        self.tab1, self.tab2, self.tab3 = ttk.Frame(self.tab_control), ttk.Frame(self.tab_control), ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab1, text="🔍 Scraper Settings")
        self.tab_control.add(self.tab2, text="🤖 Human Mimicry")
        self.tab_control.add(self.tab3, text="🌐 Account")
        self.tab_control.pack(fill="x", pady=5)

        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()

        tk.Label(main_frame, text="📊 Scraped Results", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
        
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "time", "post_text", "emails", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name"); self.tree.heading("time", text="Time")
        self.tree.heading("post_text", text="Post Text"); self.tree.heading("emails", text="Emails")
        self.tree.heading("status", text="Matched")

        self.tree.column("name", width=150); self.tree.column("time", width=100)
        self.tree.column("post_text", width=400); self.tree.column("emails", width=150); self.tree.column("status", width=80)

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")

    def setup_tab1(self):
        tk.Label(self.tab1, text="Search Query:").grid(row=0, column=0, sticky="w", pady=5)
        self.search_query = tk.Entry(self.tab1, width=50); self.search_query.insert(0, self.config['scraper_settings'].get('search_query', '')); self.search_query.grid(row=0, column=1, padx=10)
        
        tk.Label(self.tab1, text="Keywords (comma sep):").grid(row=1, column=0, sticky="nw", pady=5)
        self.keywords_txt = tk.Text(self.tab1, width=37, height=3); self.keywords_txt.insert("1.0", ", ".join(self.config['scraper_settings'].get('keywords', []))); self.keywords_txt.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.tab1, text="Time Filter:").grid(row=2, column=0, sticky="w", pady=5)
        self.time_filter_cb = ttk.Combobox(self.tab1, values=["Past_24_hours", "Past_week", "Past_month", "none"]); self.time_filter_cb.set("Past_24_hours"); self.time_filter_cb.grid(row=2, column=1, padx=10, sticky="w")

        tk.Label(self.tab1, text="Sort By:").grid(row=3, column=0, sticky="w", pady=5)
        self.sort_by_cb = ttk.Combobox(self.tab1, values=["latest", "top"]); self.sort_by_cb.set("latest"); self.sort_by_cb.grid(row=3, column=1, padx=10, sticky="w")

        tk.Label(self.tab1, text="Category:").grid(row=4, column=0, sticky="w", pady=5)
        self.category_cb = ttk.Combobox(self.tab1, values=["Posts", "Jobs", "People"]); self.category_cb.set("Posts"); self.category_cb.grid(row=4, column=1, padx=10, sticky="w")

    def setup_tab2(self):
        self.mouse_move = tk.BooleanVar(value=True); tk.Checkbutton(self.tab2, text="Enable Mouse Curves", variable=self.mouse_move).pack(anchor="w", pady=5)

    def setup_tab3(self):
        tk.Label(self.tab3, text="LinkedIn Email:").pack(anchor="w"); self.email_ent = tk.Entry(self.tab3, width=40); self.email_ent.pack(anchor="w", pady=5)
        tk.Label(self.tab3, text="LinkedIn Password:").pack(anchor="w"); self.pass_ent = tk.Entry(self.tab3, show="*", width=40); self.pass_ent.pack(anchor="w", pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, f">> {message}\n"); self.log_area.see(tk.END)

    def start_scraping_thread(self):
        self.run_btn.config(state="disabled")
        threading.Thread(target=self.run_scraper, daemon=True).start()

    def run_scraper(self):
        try:
            user_email = self.email_ent.get()
            user_pass = self.pass_ent.get()

            if not user_email or not user_pass:
                messagebox.showwarning("Input Error", "Please enter LinkedIn Email and Password in 'Account' tab!")
                self.run_btn.config(state="normal")
                return
            
            os.environ["LINKEDIN_USERNAME"] = user_email
            os.environ["LINKEDIN_PASSWORD"] = user_pass
            scraper = LinkedInScraper(self.config)

            
            current_kw = [k.strip().lower() for k in self.keywords_txt.get("1.0", tk.END).split(",") if k.strip()]
            self.config['scraper_settings'].update({
                'search_query': self.search_query.get(), 
                'category': self.category_cb.get(), 
                'time_filter': self.time_filter_cb.get(), 
                'sort_by_date': self.sort_by_cb.get(), 
                'keywords': current_kw
            })
            
            scraper = LinkedInScraper(self.config)
            self.log("🔑 Logging in..."); scraper.login()
            self.log("🔎 Searching..."); scraper.perform_search()
            self.log("🎯 Applying Filters..."); scraper.select_category_from_config(); scraper.apply_all_filters()
            self.log("📜 Scrolling..."); scraper.human_like_scroll()
            
            # Scraper advanced extraction use karega (Strategies wala)
            scraped_data = scraper.extract_post_elements()
            for item in self.tree.get_children(): self.tree.delete(item)

            processed_posts = []
            for post in scraped_data:
                txt = post.get("Post Text", "")
                emails = extract_emails_from_text(txt)
                
                # --- FIXED: Scraper.py se Timestamp uthaya gaya hai ---
                p_time = post.get("Timestamp")
                if not p_time or p_time == "[Unknown Time]":
                    p_time = "Recent"

                matched = "True" if any(k in txt.lower() for k in current_kw) else "False"

                self.tree.insert("", "end", values=(
                    post.get("Author Name", "N/A"), 
                    p_time, 
                    txt[:60] + "...", 
                    ", ".join(emails) if emails else "None", 
                    matched
                ))
                
                processed_posts.append({
                    "Name": post.get("Author Name", "N/A"),
                    "Time": p_time,
                    "Post Text": txt,
                    "Emails Found": emails,
                    "Match Status": matched
                })

            export_data(processed_posts, self.search_query.get(), self.category_cb.get())
            
            self.log(f"✅ Success! Only 2 files (CSV & JSON) saved in output.")
            scraper.close()
            messagebox.showinfo("Done", "Scraping Finished! Check output folder for 2 files.")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
        finally:
            self.run_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk(); app = LinkedInScraperGUI(root); root.mainloop()