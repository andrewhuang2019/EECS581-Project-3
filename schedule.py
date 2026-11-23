"""
schedule_input.py

A window where the user enters their class schedule. It saves to schedule.json
so another Python program can read it.

Run it:            python schedule_input.py
Read it elsewhere: from schedule_input import load_schedule
                   classes = load_schedule()      # list of dicts
                   (or just json.load(open("schedule.json")))

Each class is saved as:
    {"name": "Calculus 101", "days": ["Mon", "Wed", "Fri"],
     "start": "10:00", "end": "10:50"}          # 24-hour HH:MM
"""

import json
import re

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # lets other programs import load_schedule() without Tk installed
    tk = None

SCHEDULE_FILE = "schedule.json"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})\s*(am|pm)?$", re.IGNORECASE)
SUFFIX = re.compile(r"(am|pm)$", re.IGNORECASE)
PRESETS = {"M W F": ["Mon", "Wed", "Fri"], "T Th": ["Tue", "Thu"], "M-F": DAY_NAMES[:5], "Clear": []}
COLORS = ["#cfe8ff", "#ffd9c7", "#d5f0d0", "#f1d7f5", "#fff3b8", "#cdeee9", "#ffd1dc", "#e0e0f8"]


# ---------- file access (use these from your other program) ----------
def load_schedule(path=SCHEDULE_FILE):
    with open(path) as f:
        return json.load(f)


def save_schedule(classes, path=SCHEDULE_FILE):
    with open(path, "w") as f:
        json.dump(classes, f, indent=2)


# ---------- time helpers ----------
def parse_time(text):
    """'10:00am' / '2:30pm' -> minutes since midnight. Raises ValueError."""
    m = TIME_PATTERN.match(text.strip())
    if not m:
        raise ValueError(f"Bad time '{text}'. Use a format like 10:00 or 2:30.")
    hour, minute, period = int(m.group(1)), int(m.group(2)), m.group(3)
    if minute > 59:
        raise ValueError(f"Bad minutes in '{text}'.")
    if period:
        if not 1 <= hour <= 12:
            raise ValueError(f"Bad hour in '{text}'.")
        hour = hour % 12 + (12 if period.lower() == "pm" else 0)
    elif hour > 23:
        raise ValueError(f"Bad hour in '{text}'.")
    return hour * 60 + minute


def fmt(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def to_min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def split12(minutes):
    """minutes -> ('2:30', 'PM')"""
    h = minutes // 60
    return f"{h % 12 or 12}:{minutes % 60:02d}", ("AM" if h < 12 else "PM")


def fmt12(hhmm):
    t, p = split12(to_min(hhmm))
    return f"{t} {p}"


# ---------- the window ----------
class App(tk.Tk if tk else object):
    def __init__(self):
        super().__init__()
        self.title("Class Schedule")
        self.geometry("1040x640")
        self.minsize(900, 560)
        self.classes = []
        self.editing = None  # the class being edited, or None
        self.dirty = False

        self.name_var = tk.StringVar()
        self.day_vars = {d: tk.BooleanVar() for d in DAY_NAMES}
        self.start_var, self.end_var = tk.StringVar(), tk.StringVar()
        self.start_ap, self.end_ap = tk.StringVar(value="AM"), tk.StringVar(value="AM")
        self.status = tk.StringVar()

        self._build()
        self._load()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-s>", lambda e: self.save())
        self.name_entry.focus()

    # ----- layout -----
    def _build(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        left = ttk.Frame(self, padding=12)
        left.grid(row=0, column=0, sticky="ns")
        right = ttk.Frame(self, padding=(0, 12, 12, 12))
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.form = ttk.LabelFrame(left, text="Add a class", padding=10)
        self.form.pack(fill="x")
        ttk.Label(self.form, text="Class name").grid(row=0, column=0, columnspan=4, sticky="w")
        self.name_entry = ttk.Entry(self.form, textvariable=self.name_var, width=34)
        self.name_entry.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        self.name_entry.bind("<Return>", lambda e: self.submit())

        ttk.Label(self.form, text="Days").grid(row=2, column=0, columnspan=4, sticky="w")
        days = ttk.Frame(self.form)
        days.grid(row=3, column=0, columnspan=4, sticky="w")
        for d in DAY_NAMES:
            ttk.Checkbutton(days, text=d, variable=self.day_vars[d], style="Toolbutton",
                            width=4).pack(side="left", padx=1)
        presets = ttk.Frame(self.form)
        presets.grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 8))
        ttk.Label(presets, text="Quick:").pack(side="left")
        for label, ds in PRESETS.items():
            ttk.Button(presets, text=label, width=6,
                       command=lambda ds=ds: self.set_days(ds)).pack(side="left", padx=2)

        for r, (label, var, ap) in enumerate([("Start", self.start_var, self.start_ap),
                                              ("End", self.end_var, self.end_ap)]):
            ttk.Label(self.form, text=label).grid(row=5 + r, column=0, sticky="w", pady=2)
            e = ttk.Entry(self.form, textvariable=var, width=8)
            e.grid(row=5 + r, column=1, sticky="w")
            e.bind("<Return>", lambda ev: self.submit())
            ttk.Combobox(self.form, textvariable=ap, values=["AM", "PM"], width=4,
                         state="readonly").grid(row=5 + r, column=2, sticky="w", padx=4)
        ttk.Label(self.form, text="e.g. 10:00 or 2:30", foreground="#777").grid(
            row=5, column=3, sticky="w")

        btns = ttk.Frame(self.form)
        btns.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        self.submit_btn = ttk.Button(btns, text="Add class", command=self.submit)
        self.submit_btn.pack(side="left", expand=True, fill="x")
        self.cancel_btn = ttk.Button(btns, text="Clear form", command=self.clear_form)
        self.cancel_btn.pack(side="left", padx=(6, 0))

        self.msg = tk.Label(left, textvariable=self.status, wraplength=330, justify="left",
                            anchor="w", fg="#b00020")
        self.msg.pack(fill="x", pady=6)

        lf = ttk.LabelFrame(left, text="Your classes", padding=6)
        lf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(lf, columns=("name", "days", "time"), show="headings",
                                 height=8, selectmode="browse")
        for col, text, w in (("name", "Class", 120), ("days", "Days", 90), ("time", "Time", 120)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        row = ttk.Frame(lf)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="Edit", command=self.edit_selected).pack(side="left")
        ttk.Button(row, text="Delete", command=self.delete_selected).pack(side="left", padx=4)

        top = ttk.Frame(right)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(top, text="Weekly preview", font=("TkDefaultFont", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Save schedule (Ctrl+S)", command=self.save).pack(side="right")
        ttk.Button(top, text="Delete schedule", command=self.delete_all).pack(side="right", padx=6)
        self.canvas = tk.Canvas(right, bg="white", highlightthickness=1,
                                highlightbackground="#bbb")
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.file_lbl = ttk.Label(right, foreground="#777")
        self.file_lbl.grid(row=2, column=0, sticky="w", pady=(6, 0))

    # ----- data -----
    def _load(self):
        try:
            data = load_schedule()
            for k in data:
                to_min(k["start"]), to_min(k["end"]), k["name"], k["days"]
            self.classes = data
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            messagebox.showwarning("Couldn't read schedule",
                                   f"{SCHEDULE_FILE} exists but isn't valid, so starting empty. "
                                   "It will be overwritten if you save.")
        self.classes.sort(key=self.sort_key)

    @staticmethod
    def sort_key(k):
        return (DAY_NAMES.index(k["days"][0]), k["start"])

    @staticmethod
    def overlaps(a, b):
        return bool(set(a["days"]) & set(b["days"])) and \
            to_min(a["start"]) < to_min(b["end"]) and to_min(b["start"]) < to_min(a["end"])

    def set_dirty(self, value=True):
        self.dirty = value
        self.title("Class Schedule" + (" *" if value else ""))

    def save(self):
        try:
            save_schedule(self.classes)
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return
        self.set_dirty(False)
        self.flash(f"Saved {len(self.classes)} class(es) to {SCHEDULE_FILE}", ok=True)

    def on_close(self):
        if self.dirty:
            ans = messagebox.askyesnocancel("Unsaved changes", "Save before closing?")
            if ans is None:
                return
            if ans:
                self.save()
                if self.dirty:
                    return
        self.destroy()

    # ----- form -----
    def flash(self, text, ok=False):
        self.status.set(text)
        self.msg.config(fg="#1b7f3b" if ok else "#b00020")

    def set_days(self, ds):
        for d, v in self.day_vars.items():
            v.set(d in ds)

    def read_time(self, text, ap, label):
        text = text.strip()
        if not text:
            raise ValueError(f"Enter a {label} time.")
        if text.isdigit():
            text += ":00"
        if not SUFFIX.search(text):
            text += ap
        return parse_time(text)

    def read_form(self):
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Enter a class name.")
        days = [d for d in DAY_NAMES if self.day_vars[d].get()]
        if not days:
            raise ValueError("Pick at least one day.")
        start = self.read_time(self.start_var.get(), self.start_ap.get(), "start")
        end = self.read_time(self.end_var.get(), self.end_ap.get(), "end")
        if end <= start:
            raise ValueError("End time must be after start time (check AM/PM).")
        return {"name": name, "days": days, "start": fmt(start), "end": fmt(end)}

    def submit(self):
        try:
            entry = self.read_form()
        except ValueError as e:
            self.flash(str(e))
            return
        clashes = [k["name"] for k in self.classes if k is not self.editing and self.overlaps(entry, k)]
        if clashes and not messagebox.askyesno(
                "Time conflict", f"This overlaps with: {', '.join(clashes)}.\n\nAdd it anyway?"):
            return
        verb = "Updated" if self.editing else "Added"
        if self.editing is None:
            self.classes.append(entry)
        else:
            self.classes[next(i for i, k in enumerate(self.classes) if k is self.editing)] = entry
        self.classes.sort(key=self.sort_key)
        self.set_dirty()
        self.clear_form()
        self.refresh()
        self.flash(f"{verb} {entry['name']}. Remember to save.", ok=True)
        self.name_entry.focus()

    def clear_form(self):
        self.editing = None
        self.name_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.start_ap.set("AM")
        self.end_ap.set("AM")
        self.set_days([])
        self.form.config(text="Add a class")
        self.submit_btn.config(text="Add class")
        self.cancel_btn.config(text="Clear form")
        self.draw()

    # ----- list actions -----
    def selected(self):
        sel = self.tree.selection()
        return self.classes[int(sel[0])] if sel else None

    def edit_selected(self):
        k = self.selected()
        if k:
            self.load_into_form(k)
        else:
            self.flash("Select a class in the list first.")

    def load_into_form(self, k):
        self.editing = k
        self.name_var.set(k["name"])
        self.set_days(k["days"])
        (st, sp), (et, ep) = split12(to_min(k["start"])), split12(to_min(k["end"]))
        self.start_var.set(st)
        self.start_ap.set(sp)
        self.end_var.set(et)
        self.end_ap.set(ep)
        self.form.config(text=f"Editing: {k['name']}")
        self.submit_btn.config(text="Update class")
        self.cancel_btn.config(text="Cancel edit")
        self.status.set("")
        self.draw()

    def delete_selected(self):
        k = self.selected()
        if not k:
            self.flash("Select a class in the list first.")
            return
        if messagebox.askyesno("Delete class", f"Delete '{k['name']}'?"):
            self.classes.remove(k)
            if self.editing is k:
                self.clear_form()
            self.set_dirty()
            self.refresh()

    def delete_all(self):
        if not self.classes:
            self.flash("There are no classes to delete.")
            return
        if not messagebox.askyesno(
                "Delete schedule",
                f"Delete all {len(self.classes)} class(es)?\n\n"
                f"This also clears {SCHEDULE_FILE} and can't be undone.",
                icon="warning"):
            return
        self.classes = []
        self.clear_form()
        self.refresh()
        self.set_dirty()
        self.save()
        if not self.dirty:
            self.flash("Schedule deleted.", ok=True)

    # ----- display -----
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, k in enumerate(self.classes):
            self.tree.insert("", "end", iid=str(i), values=(
                k["name"], " ".join(k["days"]), f"{fmt12(k['start'])} - {fmt12(k['end'])}"))
        self.file_lbl.config(text=f"File: {SCHEDULE_FILE}   |   {len(self.classes)} class(es)")
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        days = DAY_NAMES[:5] + [d for d in DAY_NAMES[5:] if any(d in k["days"] for k in self.classes)]
        lo, hi = 8 * 60, 17 * 60
        if self.classes:
            lo = min(lo, min(to_min(k["start"]) for k in self.classes) // 60 * 60)
            hi = max(hi, -(-max(to_min(k["end"]) for k in self.classes) // 60) * 60)
        left, top, pad = 58, 28, 8
        colw = (w - left - pad) / len(days)
        y = lambda m: top + (m - lo) / (hi - lo) * (h - top - pad)

        for i, d in enumerate(days):
            c.create_text(left + colw * (i + 0.5), top / 2, text=d, fill="#111",
                          font=("TkDefaultFont", 10, "bold"))
            c.create_line(left + colw * i, top, left + colw * i, h - pad, fill="#ddd")
        c.create_line(left + colw * len(days), top, left + colw * len(days), h - pad, fill="#ddd")
        for m in range(lo, hi + 1, 60):
            c.create_line(left, y(m), w - pad, y(m), fill="#e6e6e6")
            t, p = split12(m)
            c.create_text(left - 6, y(m), text=f"{t.split(':')[0]} {p}", anchor="e", fill="#666")

        for idx, k in enumerate(self.classes):
            color = COLORS[idx % len(COLORS)]
            for d in k["days"]:
                x0 = left + colw * days.index(d) + 2
                y0, y1 = y(to_min(k["start"])), y(to_min(k["end"]))
                tag = f"cls{idx}_{d}"
                active = k is self.editing
                c.create_rectangle(x0, y0, x0 + colw - 4, y1, fill=color, tags=tag,
                                   outline="#333" if active else "#999", width=3 if active else 1)
                c.create_text(x0 + 5, y0 + 4, anchor="nw", width=colw - 14, tags=tag, fill="#111",
                              text=f"{k['name']}\n{fmt12(k['start'])}-{fmt12(k['end'])}",
                              font=("TkDefaultFont", 9))
                c.tag_bind(tag, "<Button-1>", lambda e, k=k: self.load_into_form(k))
                c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
                c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

        if not self.classes:
            c.create_text(w / 2, h / 2, text="No classes yet.\nAdd one on the left.",
                          fill="#999", justify="center", font=("TkDefaultFont", 12))


def main():
    if tk is None:
        raise SystemExit("Tkinter isn't installed. On Linux: sudo apt install python3-tk")
    App().mainloop()


if __name__ == "__main__":
    main()