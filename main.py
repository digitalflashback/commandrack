import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math

SIDEBAR_WIDTH = 300
MIN_WIDTH = 24
MAX_INLINE_LINES = 10
DOCS_FOLDER = "docs"


class SidebarApp:
    def __init__(self, root):
        self.root = root
        self.side = "right"
        self.collapsed = False

        os.makedirs(DOCS_FOLDER, exist_ok=True)

        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        root.geometry(f"{SIDEBAR_WIDTH}x{screen_h}+{screen_w - SIDEBAR_WIDTH}+0")
        root.configure(bg="#1E1E2F")

        # ---- Sidebar Frame ----
        self.sidebar = tk.Frame(root, bg="#1E1E2F")
        self.sidebar.pack(fill=tk.BOTH, expand=True)

        # ---- Top bar ----
        self.bar = tk.Frame(self.sidebar, bg="#282C34", height=30)
        self.bar.pack(fill=tk.X)

        # ---- Collapse, Pin, Close gombok ----
        self.collapse_btn = tk.Button(self.bar, text="▶", command=self.toggle_sidebar, bg="#61AFEF")
        self.pin_btn = tk.Button(self.bar, text="⇄", command=self.toggle_side, bg="#61AFEF")
        self.close_btn = tk.Button(self.bar, text="✕", command=root.destroy, bg="#E06C75")
        self.update_top_buttons()

        # ---- Search bar + Add category ----
        search_frame = tk.Frame(self.sidebar, bg="#1E1E2F")
        search_frame.pack(fill=tk.X, padx=4, pady=4)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.refresh)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.focus_set()
        tk.Button(search_frame, text="+", command=self.add_category, bg="#61AFEF").pack(side=tk.RIGHT, padx=2)

        # ---- Scrollable content ----
        frame = tk.Frame(self.sidebar)
        frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(frame, bg="#1E1E2F", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(self.canvas, bg="#1E1E2F")
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window_id, width=e.width))

        # ---- Mouse wheel ----
        root.bind_all("<MouseWheel>", self._on_mousewheel_global)
        root.bind_all("<Button-4>", self._on_mousewheel_global)
        root.bind_all("<Button-5>", self._on_mousewheel_global)

        self.restore_btn = None
        self.docs = self.load_docs()
        self.refresh()

    # ---------- Top button dinamikus update ----------
    def update_top_buttons(self):
        self.collapse_btn.pack_forget()
        self.pin_btn.pack_forget()
        self.close_btn.pack_forget()

        if self.side == "left":
            self.pin_btn.pack(side=tk.LEFT)
            self.collapse_btn.pack(side=tk.RIGHT)

            # FIX: padx nem lehet negatív
            padx = max(0, self.root.winfo_width() - SIDEBAR_WIDTH)
            self.close_btn.pack(side=tk.LEFT, padx=padx)
        else:
            self.collapse_btn.pack(side=tk.LEFT)
            self.pin_btn.pack(side=tk.RIGHT)
            self.close_btn.pack(side=tk.RIGHT)

        self.collapse_btn.config(text="◀" if self.side == "left" else "▶")

    # ---------- Mouse wheel ----------
    def _on_mousewheel_global(self, event):
        widget = event.widget
        while widget:
            if widget is self.sidebar:
                if event.delta:
                    self.canvas.yview_scroll(int(-event.delta / 120), "units")
                elif event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
                return
            widget = widget.master

    # ---------- Load docs ----------
    def load_docs(self):
        docs = {}
        for fname in os.listdir(DOCS_FOLDER):
            if not fname.endswith(".txt"):
                continue
            with open(os.path.join(DOCS_FOLDER, fname), encoding="utf-8") as f:
                lines = f.read().splitlines()
            items, block = [], []
            def flush():
                if block:
                    items.append((block[0], "\n".join(block[1:])))
            for line in lines:
                if not line.strip():
                    flush()
                    block = []
                else:
                    block.append(line)
            flush()
            docs[fname[:-4]] = items
        return docs

    # ---------- Sidebar controls ----------
    def toggle_side(self):
        self.side = "left" if self.side == "right" else "right"
        width = MIN_WIDTH if self.collapsed else SIDEBAR_WIDTH
        x = 0 if self.side == "left" else self.root.winfo_screenwidth() - width
        h = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{h}+{x}+0")
        self.update_top_buttons()
        if self.collapsed and self.restore_btn:
            self.restore_btn.config(text="▶" if self.side == "left" else "◀")

    def toggle_sidebar(self):
        h = self.root.winfo_screenheight()
        if not self.collapsed:
            self.collapsed = True
            self.sidebar.pack_forget()
            x = 0 if self.side == "left" else self.root.winfo_screenwidth() - MIN_WIDTH
            self.root.geometry(f"{MIN_WIDTH}x{h}+{x}+0")
            self.show_restore_btn()
            self.collapse_btn.pack_forget()
        else:
            self.restore_sidebar()

    def show_restore_btn(self):
        self.restore_btn = tk.Button(
            self.root,
            text="▶" if self.side == "left" else "◀",
            command=self.restore_sidebar,
            bg="#61AFEF"
        )
        self.restore_btn.place(x=0, y=10, width=MIN_WIDTH, height=30)

    def restore_sidebar(self):
        if self.restore_btn:
            self.restore_btn.destroy()
            self.restore_btn = None
        h = self.root.winfo_screenheight()
        x = 0 if self.side == "left" else self.root.winfo_screenwidth() - SIDEBAR_WIDTH
        self.root.geometry(f"{SIDEBAR_WIDTH}x{h}+{x}+0")
        self.sidebar.pack(fill=tk.BOTH, expand=True)
        self.collapsed = False
        self.update_top_buttons()

    # ---------- Refresh ----------
    def refresh(self, *_):
        for w in self.inner.winfo_children():
            w.destroy()
        q = self.search_var.get().lower()
        for block, items in self.docs.items():
            visible = [(c, d) for c, d in items if not q or q in c.lower() or q in d.lower()]
            if not visible:
                continue

            frame_block = tk.Frame(self.inner, bg="#1E1E2F")
            frame_block.pack(fill=tk.X, anchor="w", padx=2)

            tk.Label(frame_block, text=block, fg="#61AFEF", bg="#1E1E2F",
                     font=("monospace", 10, "bold"), justify="left", anchor="w",
                     wraplength=SIDEBAR_WIDTH - 60).pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Button(frame_block, text="✎", command=lambda b=block: self.edit_category(b),
                      bg="#1E1E2F", fg="white", activebackground="#282C34",
                      relief="flat", bd=0, highlightthickness=0, padx=0, pady=0).pack(side=tk.RIGHT, padx=2)

            for cmd, desc in visible:
                self.add_command(cmd, desc)

    # ---------- Add/Edit category ----------
    def add_category(self):
        name = simpledialog.askstring("Új kategória", "Kategória neve:")
        if name:
            path = os.path.join(DOCS_FOLDER, f"{name}.txt")
            if os.path.exists(path):
                messagebox.showerror("Hiba", "Már létezik ilyen kategória!")
                return
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            self.docs = self.load_docs()
            self.refresh()

    def edit_category(self, block):
        path = os.path.join(DOCS_FOLDER, f"{block}.txt")
        if not os.path.exists(path):
            messagebox.showerror("Hiba", "Fájl nem található!")
            return

        w = tk.Toplevel(self.root)
        w.title(f"Szerkesztés: {block}")
        w.geometry("400x400")

        btn_frame = tk.Frame(w)
        btn_frame.pack(fill=tk.X, padx=4, pady=4)
        tk.Button(btn_frame, text="Mentés", command=lambda: save(),
                  bg="#61AFEF").pack(side=tk.LEFT)

        tk.Label(w, text="Kategória név:").pack(anchor="w", padx=4, pady=2)
        name_var = tk.StringVar(value=block)
        name_entry = tk.Entry(w, textvariable=name_var)
        name_entry.pack(fill=tk.X, padx=4, pady=2)

        tk.Label(w, text="Tartalom:").pack(anchor="w", padx=4, pady=2)
        text = tk.Text(w, wrap="word")
        with open(path, "r", encoding="utf-8") as f:
            text.insert("1.0", f.read())
        text.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        def save():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Hiba", "Név nem lehet üres!")
                return
            new_path = os.path.join(DOCS_FOLDER, f"{new_name}.txt")
            if new_name != block:
                if os.path.exists(new_path):
                    messagebox.showerror("Hiba", "Már létezik ilyen kategória!")
                    return
                os.rename(path, new_path)
                path_to_save = new_path
            else:
                path_to_save = path
            with open(path_to_save, "w", encoding="utf-8") as f:
                f.write(text.get("1.0", "end").rstrip())
            self.docs = self.load_docs()
            self.refresh()
            w.destroy()

    # ---------- Add command block ----------
    def add_command(self, cmd, desc):
        box = tk.Frame(self.inner, bg="#282C34")
        box.pack(fill=tk.X, padx=4, pady=2)
        header = tk.Frame(box, bg="#282C34")
        header.pack(fill=tk.X)

        label = tk.Label(header, text=cmd, fg="#ABB2BF", bg="#282C34",
                         font=("monospace", 10, "bold"), anchor="w",
                         justify="left", wraplength=SIDEBAR_WIDTH - 60)
        label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        tk.Button(header, text="📋", command=lambda: self.copy_text(desc),
                  bg="#282C34", fg="white", activebackground="#3E4451",
                  relief="flat", bd=0, highlightthickness=0, padx=0, pady=0).pack(side=tk.RIGHT, padx=2)

        body = tk.Frame(box, bg="#3E4451")
        lines = desc.splitlines()
        preview = "\n".join(lines[:MAX_INLINE_LINES])

        txt_widget = tk.Text(body, bg="#3E4451", fg="#C8CCD4",
                             font=("monospace", 10), wrap="word",
                             borderwidth=0, highlightthickness=0)
        txt_widget.insert("1.0", preview)

        wrap_chars = max(1, (SIDEBAR_WIDTH - 20) // 7)
        total_lines = 0
        for line in preview.splitlines():
            total_lines += max(1, math.ceil(len(line) / wrap_chars))
        total_lines = min(total_lines, MAX_INLINE_LINES)
        txt_widget.config(height=total_lines, state="disabled")
        txt_widget.pack(fill=tk.X, padx=4, pady=2)

        if len(lines) > MAX_INLINE_LINES:
            tk.Button(body, text="🔍 Részletek", command=lambda: self.detail(cmd, desc),
                      bg="#61AFEF").pack(anchor="e", padx=4, pady=2)

        def toggle(_=None):
            if body.winfo_ismapped():
                body.pack_forget()
            else:
                body.pack(fill=tk.X, padx=4, pady=2)

        header.bind("<Button-1>", toggle)
        label.bind("<Button-1>", toggle)

    # ---------- Utils ----------
    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def detail(self, title, text):
        w = tk.Toplevel(self.root)
        w.title(title)
        t = tk.Text(w, wrap="word")
        t.insert("1.0", text)
        t.config(state="disabled")
        t.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    SidebarApp(root)
    root.mainloop()
