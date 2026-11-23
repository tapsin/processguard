import ctypes
import os
import subprocess
import sys
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk, messagebox

import psutil


def elevate():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    return False


_kernel32 = ctypes.windll.kernel32
_user32 = ctypes.windll.user32


def file_description(path):
    """Windows sürüm kaynağından programın görünen adını okur."""
    if not path or not os.path.isfile(path):
        return ""
    try:
        size = _kernel32.GetFileVersionInfoSizeW(path, None)
        if not size:
            return ""
        buf = ctypes.create_string_buffer(size)
        if not _kernel32.GetFileVersionInfoW(path, 0, size, buf):
            return ""
        lang_ptr = ctypes.c_void_p()
        lang_len = wintypes.UINT()
        if not _kernel32.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(lang_ptr), ctypes.byref(lang_len)):
            return ""
        lang, charset = ctypes.cast(lang_ptr, ctypes.POINTER(wintypes.WORD))[0], ctypes.cast(lang_ptr, ctypes.POINTER(wintypes.WORD))[1]
        block = f"\\StringFileInfo\\{lang:04x}{charset:04x}\\FileDescription"
        val_ptr = ctypes.c_void_p()
        val_len = wintypes.UINT()
        if _kernel32.VerQueryValueW(buf, block, ctypes.byref(val_ptr), ctypes.byref(val_len)) and val_len.value:
            return ctypes.wstring_at(val_ptr).strip()
    except Exception:
        pass
    return ""


def window_title(pid):
    """İşlemin ana pencere başlığını döndürür (uygulama adı genelde burada görünür)."""
    result = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        p = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and _user32.IsWindowVisible(hwnd):
            n = _user32.GetWindowTextLengthW(hwnd)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                _user32.GetWindowTextW(hwnd, b, n + 1)
                if b.value.strip():
                    result.append(b.value.strip())
        return True

    try:
        _user32.EnumWindows(EnumWindowsProc(cb), 0)
    except Exception:
        pass
    return result[0] if result else ""


def parent_label(proc, by_pid):
    """Sürecin üst program zincirini 'ana > alt' biçiminde döndürür."""
    try:
        chain = []
        cur = proc
        seen = set()
        for _ in range(12):
            try:
                ppid = cur.ppid()
            except Exception:
                break
            if not ppid or ppid in seen:
                break
            seen.add(ppid)
            parent = by_pid.get(ppid)
            if parent is None:
                try:
                    parent = psutil.Process(ppid)
                except Exception:
                    break
            try:
                label = parent.info.get("name") if getattr(parent, "info", None) else parent.name()
            except Exception:
                break
            chain.append(label or "?")
            if ppid <= 4:
                break
            cur = parent
        return " › ".join(chain) if chain else "-"
    except Exception:
        return "-"


def friendly_name(proc):
    try:
        info = proc.info
        name = info.get("name") or "?"
        exe = info.get("exe") or ""
        cmd = info.get("cmdline") or ""
        pid = info.get("pid")

        desc = file_description(exe)
        if not desc and pid:
            desc = window_title(pid)
        if not desc and exe:
            desc = os.path.splitext(os.path.basename(exe))[0]
        if not desc and cmd:
            parts = [p for p in cmd.split('"') if p.strip()]
            desc = os.path.splitext(os.path.basename(parts[0] if parts else cmd[:80]))[0] or cmd[:80]
        if not desc:
            desc = name
        return name, desc, exe or cmd[:120]
    except Exception:
        try:
            return proc.name(), proc.name(), ""
        except Exception:
            return "?", "?", ""


class ProcessGuard:
    def __init__(self, root):
        self.root = root
        self.root.title("ProcessGuard - Görev Yöneticisi")
        self.root.geometry("1100x640")
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.build_ui()
        self.refresh()

    def build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Filtre:").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(top, textvariable=self.search, width=36).pack(side="left", padx=6)
        ttk.Button(top, text="Yenile", command=self.refresh).pack(side="left", padx=4)
        ttk.Button(top, text="Seçiliyi Sonlandır", command=self.kill).pack(side="left", padx=4)
        ttk.Button(top, text="Görev Yöneticisi", command=self.open_tm).pack(side="left", padx=4)
        self.count = ttk.Label(top, text="")
        self.count.pack(side="right")

        frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frame.pack(fill="both", expand=True)
        cols = ("pid", "name", "program", "parent", "cpu", "mem", "path")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, text, width in [
            ("pid", "PID", 80),
            ("name", "İşlem", 180),
            ("program", "Bağlı Program", 260),
            ("parent", "Üst Program Ağacı", 300),
            ("cpu", "CPU %", 80),
            ("mem", "Bellek MB", 100),
            ("path", "Konum / Komut", 320),
        ]:
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.rows = []

    def collect(self):
        result = []
        procs = list(psutil.process_iter(["pid", "name", "exe", "cmdline"]))
        by_pid = {}
        for p in procs:
            try:
                by_pid[p.info["pid"]] = p
            except Exception:
                continue
        for p in procs:
            try:
                name, program, path = friendly_name(p)
                parent = parent_label(p, by_pid)
                try:
                    cpu = p.cpu_percent(interval=None)
                except Exception:
                    cpu = 0.0
                try:
                    mem = p.memory_info().rss / (1024 * 1024)
                except Exception:
                    mem = 0.0
                result.append((p.info["pid"], name, program, parent, f"{cpu:.1f}", f"{mem:.1f}", path))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result

    def refresh(self):
        query = self.search.get().strip().lower()
        self.rows = self.collect()
        shown = [r for r in self.rows if not query or any(query in str(v).lower() for v in r[:3])]
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in shown:
            self.tree.insert("", "end", values=r)
        self.count.config(text=f"{len(shown)} / {len(self.rows)} işlem")

    def sort_by(self, col):
        idx = ("pid", "name", "program", "parent", "cpu", "mem", "path").index(col)
        self.rows.sort(key=lambda r: float(r[idx]) if col in ("pid", "cpu", "mem") else str(r[idx]).lower())
        query = self.search.get().strip().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in self.rows:
            if not query or any(query in str(v).lower() for v in r[:3]):
                self.tree.insert("", "end", values=r)

    def kill(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Seçim yok", "Sonlandırmak için bir işlem seçin.")
            return
        killed, failed = [], []
        for item in sel:
            vals = self.tree.item(item, "values")
            pid = int(vals[0])
            name = vals[1]
            try:
                p = psutil.Process(pid)
                p.terminate()
                killed.append(f"{name} ({pid})")
            except Exception as e:
                failed.append(f"{name} ({pid}): {e}")
        if failed:
            messagebox.showwarning("Kısmen tamamlandı", "Sonlandırılamadı:\n" + "\n".join(failed))
        elif killed:
            messagebox.showinfo("Tamamlandı", "Sonlandırıldı:\n" + "\n".join(killed))
        self.refresh()

    def open_tm(self):
        subprocess.Popen(["taskmgr.exe"], shell=True)


if __name__ == "__main__":
    if not elevate():
        sys.exit(0)
    root = tk.Tk()
    ProcessGuard(root)
    root.mainloop()
