#!/usr/bin/env python3
 
"""
File Finder - Cross-platform utility to search for files and reveal them in the file explorer.
 
"""
 
import os
import subprocess
import platform
import difflib
from pathlib import Path
from datetime import datetime
 
from tkinter import (
    Tk, Frame, Label, Entry, Button, Listbox, Scrollbar,
    filedialog, messagebox, StringVar, Text, END, BOTH, LEFT, RIGHT, Y, X, W
)
from tkinter.ttk import Progressbar, Style
 
import threading
 
 
class FileFinder:
    def __init__(self, root):
        self.root = root
 
        # Color Theme
        self.BG = "#2b2d31"
        self.FG = "#f2f3f5"
        self.ENTRY_BG = "#383a40"
        self.ACCENT = "#5865F2"
        self.SECONDARY_BG = "#313338"
 
        self.file_types = StringVar(value="*")
 
        # Create custom title bar BEFORE UI
        self._create_title_bar()
 
        # Center window BEFORE building UI
        self._center_window(900, 600)
 
        # Style
        self.style = Style()
        self.style.theme_use("clam")
        self.style.configure(
            "TProgressbar",
            troughcolor=self.SECONDARY_BG,
            background=self.ACCENT,
            thickness=18,
        )
 
        # Variables
        self.folder_path = StringVar()
        self.file_name = StringVar()
        self.search_results = []
        self.is_searching = False
        self.cancel_search = False
        self.MAX_RESULTS = 1000
 
        self._build_ui()
 
    # ---------------------------------------------------------
    # CENTER WINDOW
    # ---------------------------------------------------------
    def _center_window(self, width=900, height=550):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
 
        x = int((screen_w / 2) - (width / 2))
        y = int((screen_h / 2) - (height / 2))
 
        self.root.geometry(f"{width}x{height}+{x}+{y}")
 
    # ---------------------------------------------------------
    # CUSTOM TITLE BAR
    # ---------------------------------------------------------
    def _create_title_bar(self):
        self.root.overrideredirect(True)
 
        self.title_bar = Frame(self.root, bg=self.BG, height=32)
        self.title_bar.pack(fill=X, side="top")
 
        self.title_label = Label(
            self.title_bar,
            text="File Finder",
            bg=self.BG,
            fg=self.FG,
            padx=10,
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side=LEFT, pady=5)
 
        # Close button
        self.close_btn = Button(
            self.title_bar,
            text="✕",
            bg=self.BG,
            fg=self.FG,
            bd=0,
            padx=10,
            font=("Segoe UI", 12),
            command=self.root.destroy,
            activebackground="#c9302c"
        )
        self.close_btn.pack(side=RIGHT)
 
        # Dragging support
        for widget in (self.title_bar, self.title_label):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<ButtonRelease-1>", self._stop_move)
            widget.bind("<B1-Motion>", self._on_move)
 
    def _start_move(self, event):
        self.x = event.x
        self.y = event.y
 
    def _stop_move(self, event):
        self.x = None
        self.y = None
 
    def _on_move(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.root.geometry(f"+{x}+{y}")
 
    def _minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(10, lambda: self.root.overrideredirect(True))
 
    # ---------------------------------------------------------
    # MAIN UI
    # ---------------------------------------------------------
    def _build_ui(self):
        main_frame = Frame(self.root, padx=15, pady=15, bg=self.BG)
        main_frame.pack(fill=BOTH, expand=True)
 
        # Folder selection
        folder_frame = Frame(main_frame, bg=self.BG)
        folder_frame.pack(fill=X, pady=(0, 5))
 
        Label(folder_frame, text="Search Folder:", width=12, anchor=W, fg=self.FG, bg=self.BG).pack(side=LEFT)
        Entry(folder_frame, textvariable=self.folder_path, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG)\
            .pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        Button(folder_frame, text="Browse...", command=self._browse_folder, width=10,
               bg=self.ACCENT, fg=self.FG).pack(side=RIGHT)
 
        # File name input
        name_frame = Frame(main_frame, bg=self.BG)
        name_frame.pack(fill=X, pady=(0, 5))
 
        # File type filter
        type_frame = Frame(main_frame, bg=self.BG)
        type_frame.pack(fill=X, pady=(0, 5))
 
        Label(type_frame, text="File Type:", width=12, anchor=W,
            fg=self.FG, bg=self.BG).pack(side=LEFT)
 
        Entry(
            type_frame,
            textvariable=self.file_types,
            bg=self.ENTRY_BG,
            fg=self.FG,
            insertbackground=self.FG
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
 
        Label(name_frame, text="File Name:", width=12, anchor=W, fg=self.FG, bg=self.BG).pack(side=LEFT)
        self.name_entry = Entry(name_frame, textvariable=self.file_name, bg=self.ENTRY_BG,
                                fg=self.FG, insertbackground=self.FG)
        self.name_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        self.name_entry.bind("<Return>", lambda e: self._start_search())
 
        # Buttons
        btn_frame = Frame(name_frame, bg=self.BG)
        btn_frame.pack(side=RIGHT)
 
        self.search_btn = Button(btn_frame, text="Search", command=self._start_search,
                                 width=10, bg=self.ACCENT, fg=self.FG)
        self.search_btn.pack(side=LEFT, padx=(0, 5))
 
        self.cancel_btn = Button(btn_frame, text="Cancel", command=self._cancel_search,
                                 width=10, bg="#d9534f", fg=self.FG, state="disabled")
        self.cancel_btn.pack(side=LEFT)
 
        # Progress bar
        self.progress = Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=X, pady=(5, 10))
 
        # Status label
        self.status_var = StringVar(value="Enter a folder and file name to search")
        Label(main_frame, textvariable=self.status_var, anchor=W, fg=self.FG, bg=self.BG).pack(fill=X)
 
        # Split frame
        split_frame = Frame(main_frame, bg=self.BG)
        split_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
 
        # Results list
        results_frame = Frame(split_frame, bg=self.BG)
        results_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
 
        Label(results_frame, text="Results", anchor=W, fg=self.FG, bg=self.BG).pack(fill=X, pady=(0, 5))
 
        scrollbar = Scrollbar(results_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
 
        self.results_list = Listbox(
            results_frame,
            yscrollcommand=scrollbar.set,
            selectmode="single",
            bg=self.ENTRY_BG,
            fg=self.FG,
            selectbackground="#3a3a5a",
            highlightthickness=0,
            borderwidth=0
        )
        self.results_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.results_list.bind("<Double-Button-1>", lambda e: self._open_selected())
        self.results_list.bind("<<ListboxSelect>>", lambda e: self._update_preview())
 
        scrollbar.config(command=self.results_list.yview)
 
        # Preview panel
        preview_frame = Frame(split_frame, bg=self.SECONDARY_BG, padx=10, pady=10)
        preview_frame.pack(side=RIGHT, fill=BOTH, expand=True)
 
        Label(preview_frame, text="File Preview", anchor=W, fg=self.FG, bg=self.SECONDARY_BG)\
            .pack(fill=X, pady=(0, 5))
 
        self.preview_path_var = StringVar(value="Path: ")
        self.preview_size_var = StringVar(value="Size: ")
        self.preview_mtime_var = StringVar(value="Modified: ")
 
        Label(preview_frame, textvariable=self.preview_path_var, fg=self.FG, bg=self.SECONDARY_BG,
              wraplength=350, justify=LEFT).pack(fill=X)
        Label(preview_frame, textvariable=self.preview_size_var, fg=self.FG, bg=self.SECONDARY_BG)\
            .pack(fill=X)
        Label(preview_frame, textvariable=self.preview_mtime_var, fg=self.FG, bg=self.SECONDARY_BG)\
            .pack(fill=X, pady=(0, 5))
 
        self.preview_text = Text(preview_frame, bg=self.ENTRY_BG, fg=self.FG,
                                 insertbackground=self.FG, wrap="word", height=12)
        self.preview_text.pack(fill=BOTH, expand=True)
 
        # Open button
        bottom_frame = Frame(main_frame, bg=self.BG)
        bottom_frame.pack(fill=X, side="bottom")
 
        Button(main_frame, text="Open in File Explorer", command=self._open_selected,
        bg=self.ACCENT, fg=self.FG).pack(pady=(10, 0))
 
 
    # ---------------------------------------------------------
    # SEARCH LOGIC
    # ---------------------------------------------------------
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select folder to search")
        if folder:
            self.folder_path.set(folder)
 
    def _start_search(self):
        folder = self.folder_path.get().strip()
        filename = self.file_name.get().strip()
 
        if not folder:
            messagebox.showwarning("Missing Folder", "Please select a folder to search.")
            return
        if not filename:
            messagebox.showwarning("Missing File Name", "Please enter a file name to search for.")
            return
        if not Path(folder).is_dir():
            messagebox.showerror("Invalid Folder", "The specified folder does not exist.")
            return
 
        if self.is_searching:
            return
 
        self.results_list.delete(0, END)
        self.search_results.clear()
        self._clear_preview()
 
        self.is_searching = True
        self.cancel_search = False
        self.search_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress.start(10)
        self.status_var.set("Searching...")
 
        thread = threading.Thread(target=self._search, args=(folder, filename), daemon=True)
        thread.start()
 
    def _cancel_search(self):
        if self.is_searching:
            self.cancel_search = True
            self.status_var.set("Cancelling search...")
 
    def _search(self, folder: str, filename: str):
        results = []
        filename_lower = filename.lower()
 
        patterns = [p.strip().lower() for p in self.file_types.get().split(",")]
 
        # If user entered "*" → allow all files
        if "*" in patterns:
            patterns = ["*"]  # keep it as wildcard
        else:
            # Auto-fix things like "py, txt"
            patterns = [
                p if p.startswith("*.") else f"*.{p}"
                for p in patterns if p
            ]
 
        def matches_type(filename):
            # wildcard = match everything
            if patterns == ["*"]:
                return True
 
            filename = filename.lower()
 
            for pattern in patterns:
                if pattern.startswith("*."):
                    ext = pattern[1:]  # ".py"
                    if filename.endswith(ext):
                        return True
 
            return False
 
        try:
            for root, dirs, files in os.walk(folder):
                IGNORE_DIRS = {"node_modules", ".git", "__pycache__", ".venv"}
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
 
                if self.cancel_search or len(results) >= self.MAX_RESULTS:
                    break
 
                for f in files:
                    if self.cancel_search or len(results) >= self.MAX_RESULTS:
                        break
 
                    name = f.lower()
 
                    # Exact match first (fast)
                    if filename_lower in name:
                        match = True
                    else:
                        # Fuzzy match fallback
                        score = difflib.SequenceMatcher(None, filename_lower, name).ratio()
                        match = score > 0.6   # adjust threshold if needed
 
                    if match and matches_type(f):
 
                        path = Path(root) / f
                        results.append(path)
 
                        self.root.after(0, lambda p=path: self.results_list.insert(END, str(p)))
 
                        if len(results) % 50 == 0:
                            self.root.after(
                                0,
                                lambda count=len(results): self.status_var.set(f"Searching... ({count} found)")
                            )
 
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Search error: {e}"))
 
        truncated = len(results) >= self.MAX_RESULTS
        self.root.after(0, lambda: self._search_complete(results, truncated))
 
    def _search_complete(self, results: list, truncated: bool = False):
        self.is_searching = False
        self.search_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.progress.stop()
 
        self.search_results = results
       
        # Only clear if search was cancelled early
        if self.cancel_search:
            self.results_list.delete(0, END)
            for path in results:
                self.results_list.insert(END, str(path))
 
 
        count = len(results)
 
        if self.cancel_search:
            self.status_var.set(f"Search cancelled. Found {count} files.")
        elif truncated:
            self.status_var.set(
                f"Showing first {count} results (limit reached)"
            )
            messagebox.showwarning(
                "Result Limit Reached",
                f"More than {self.MAX_RESULTS} files matched.\n"
                f"Only the first {self.MAX_RESULTS} results are shown."
            )
        else:
            self.status_var.set(f"Found {count} file{'s' if count != 1 else ''}")
 
        if count == 0 and not self.cancel_search:
            messagebox.showinfo("No Results", "No matching files found.")
 
    # ---------------------------------------------------------
    # FILE OPEN + PREVIEW
    # ---------------------------------------------------------
    def _open_selected(self):
        selection = self.results_list.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a file from the results.")
            return
 
        file_path = Path(self.search_results[selection[0]])
        self._reveal_in_explorer(file_path)
 
    def _reveal_in_explorer(self, file_path: Path):
        system = platform.system()
 
        try:
            if system == "Windows":
                subprocess.run(["explorer", "/select,", str(file_path)], check=False)
 
            elif system == "Darwin":
                subprocess.run(["open", "-R", str(file_path)], check=True)
 
            elif system == "Linux":
                try:
                    subprocess.run(
                        [
                            "dbus-send", "--print-reply", "--dest=org.freedesktop.FileManager1",
                            "/org/freedesktop/FileManager1",
                            "org.freedesktop.FileManager1.ShowItems",
                            f"array:string:file://{file_path}", "string:"
                        ],
                        check=True
                    )
                    return
                except Exception:
                    pass
 
                folder = str(file_path.parent)
                managers = [
                    ["nautilus", "--select", str(file_path)],
                    ["dolphin", "--select", str(file_path)],
                    ["thunar", folder],
                    ["pcmanfm", folder],
                ]
 
                for cmd in managers:
                    try:
                        subprocess.run(cmd, check=True)
                        return
                    except Exception:
                        continue
 
                subprocess.run(["xdg-open", folder], check=True)
 
            else:
                messagebox.showwarning("Unsupported OS", f"Cannot open explorer on {system}")
 
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file explorer: {e}")
 
    def _update_preview(self):
        selection = self.results_list.curselection()
        if not selection:
            self._clear_preview()
            return
 
        file_path = Path(self.search_results[selection[0]])
 
        self.preview_path_var.set(f"Path: {file_path}")
 
        try:
            stat = file_path.stat()
            size_kb = stat.st_size / 1024
            self.preview_size_var.set(f"Size: {stat.st_size} bytes ({size_kb:.1f} KB)")
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.preview_mtime_var.set(f"Modified: {mtime}")
        except Exception:
            self.preview_size_var.set("Size: (unavailable)")
            self.preview_mtime_var.set("Modified: (unavailable)")
 
        self.preview_text.delete("1.0", END)
 
        if file_path.suffix.lower() in {".txt", ".py", ".md", ".log", ".json", ".ini", ".cfg"}:
            try:
                with file_path.open("r", encoding="utf-8", errors="replace") as f:
                    content = f.read(4000)
                self.preview_text.insert(END, content)
            except Exception as e:
                self.preview_text.insert(END, f"Could not read file: {e}")
        else:
            self.preview_text.insert(END, "Preview not available for this file type.")
 
    def _clear_preview(self):
        self.preview_path_var.set("Path: ")
        self.preview_size_var.set("Size: ")
        self.preview_mtime_var.set("Modified: ")
        self.preview_text.delete("1.0", END)
 
 
def main():
    root = Tk()
    FileFinder(root)
    root.mainloop()
 
 
if __name__ == "__main__":
    main()