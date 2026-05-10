#!/usr/bin/env python3
"""
Phil Notepad+ — A Notepad++-like text editor built with Python / tkinter.
Features: tabbed editing, syntax highlighting, line numbers, find & replace,
dark/light themes, zoom, word-wrap toggle, go-to-line, recent files,
session persistence (.tmp), and more.
"""

import json
import os
import re
import sys
import ctypes
from ctypes import wintypes
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog, font as tkfont
from typing import Any, Dict, List, Optional, Tuple

# ─── Determine base directory (works for both script and frozen exe) ───
if getattr(sys, "frozen", False):
    _BASE_DIR: str = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_SESSION_FILE: str = os.path.join(_BASE_DIR, "phil_notepad_plus.tmp")

# ─── Syntax definitions ────────────────────────────────────────────────
SYNTAX: Dict[str, Dict[str, str]] = {
    "Python": {
        "keywords": r"\b(False|None|True|and|as|assert|async|await|break|class|continue|"
                    r"def|del|elif|else|except|finally|for|from|global|if|import|in|is|"
                    r"lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b",
        "builtins": r"\b(print|len|range|int|str|float|list|dict|set|tuple|type|isinstance|"
                    r"open|input|map|filter|zip|enumerate|sorted|reversed|abs|max|min|sum|"
                    r"hasattr|getattr|setattr|super|staticmethod|classmethod|property)\b",
        "strings":  r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'|\".*?\"|\'.*?\')',
        "comments": r'(#.*?$)',
        "numbers":  r'\b(\d+\.?\d*)\b',
        "decorators": r'(@\w+)',
    },
    "C++": {
        "preprocessor": r'(^\s*#\s*(?:include|define|undef|ifdef|ifndef|if|elif|else|endif|'
                        r'pragma|error|warning|line)\b.*$)',
        "keywords": r"\b(alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|case|"
                    r"catch|char|char8_t|char16_t|char32_t|class|compl|concept|const|"
                    r"consteval|constexpr|constinit|const_cast|continue|co_await|co_return|"
                    r"co_yield|decltype|default|delete|do|double|dynamic_cast|else|enum|"
                    r"explicit|export|extern|false|float|for|friend|goto|if|inline|int|long|"
                    r"mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|"
                    r"private|protected|public|register|reinterpret_cast|requires|return|"
                    r"short|signed|sizeof|static|static_assert|static_cast|struct|switch|"
                    r"template|this|thread_local|throw|true|try|typedef|typeid|typename|"
                    r"union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b",
        "builtins": r"\b(std|cout|cin|cerr|clog|endl|string|vector|map|set|list|deque|"
                    r"array|pair|tuple|unique_ptr|shared_ptr|weak_ptr|make_unique|"
                    r"make_shared|move|forward|begin|end|size|push_back|emplace_back|"
                    r"sort|find|count|accumulate|transform|printf|scanf|malloc|free|"
                    r"nullptr|size_t|ptrdiff_t|int8_t|int16_t|int32_t|int64_t|uint8_t|"
                    r"uint16_t|uint32_t|uint64_t)\b",
        "strings":  r'(\".*?\"|\'.*?\')',
        "comments": r'(//.*?$|/\*[\s\S]*?\*/)',
        "numbers":  r'\b(\d+\.?\d*[fFuUlL]*)\b',
    },
    "JavaScript": {
        "keywords": r"\b(var|let|const|function|return|if|else|for|while|do|switch|case|"
                    r"break|continue|new|this|class|extends|import|export|default|from|"
                    r"try|catch|finally|throw|async|await|yield|typeof|instanceof|in|of|"
                    r"null|undefined|true|false|void|delete)\b",
        "builtins": r"\b(console|document|window|Math|JSON|Array|Object|String|Number|"
                    r"Date|RegExp|Promise|Map|Set|Symbol|parseInt|parseFloat|isNaN|"
                    r"setTimeout|setInterval|fetch|alert|confirm|prompt)\b",
        "strings":  r'(\".*?\"|\'.*?\'|`[\s\S]*?`)',
        "comments": r'(//.*?$|/\*[\s\S]*?\*/)',
        "numbers":  r'\b(\d+\.?\d*)\b',
    },
    "HTML": {
        "tags":     r'(</?[a-zA-Z][a-zA-Z0-9]*)',
        "attrs":    r'\b([a-zA-Z\-]+)(?==)',
        "strings":  r'(\".*?\"|\'.*?\')',
        "comments": r'(<!--[\s\S]*?-->)',
    },
    "CSS": {
        "selectors": r'([.#]?[a-zA-Z][\w-]*)\s*(?=\{)',
        "properties": r'\b(color|background|margin|padding|border|font|display|position|'
                      r'width|height|top|left|right|bottom|flex|grid|align|justify|text|'
                      r'overflow|opacity|transition|transform|animation|z-index|cursor|'
                      r'box-shadow|outline|content|visibility|float|clear)\b',
        "strings":  r'(\".*?\"|\'.*?\')',
        "comments": r'(/\*[\s\S]*?\*/)',
        "numbers":  r'(\d+\.?\d*(px|em|rem|%|vh|vw|pt|cm|mm)?)',
    },
    "JSON": {
        "keys":     r'(\"[^\"]*?\")\s*:',
        "strings":  r':\s*(\"[^\"]*?\")',
        "numbers":  r'\b(\d+\.?\d*)\b',
        "keywords": r'\b(true|false|null)\b',
    },
    "SQL": {
        "keywords": r"\b(?i)(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|"
                    r"CREATE|DROP|ALTER|TABLE|INDEX|VIEW|JOIN|INNER|LEFT|RIGHT|OUTER|"
                    r"ON|AND|OR|NOT|IN|BETWEEN|LIKE|IS|NULL|AS|ORDER|BY|GROUP|HAVING|"
                    r"LIMIT|OFFSET|UNION|EXISTS|DISTINCT|COUNT|SUM|AVG|MAX|MIN|CASE|"
                    r"WHEN|THEN|ELSE|END|BEGIN|COMMIT|ROLLBACK|GRANT|REVOKE)\b",
        "strings":  r'(\".*?\"|\'.*?\')',
        "comments": r'(--.*?$|/\*[\s\S]*?\*/)',
        "numbers":  r'\b(\d+\.?\d*)\b',
    },
    "Markdown": {
        "headings":    r'(^#{1,6}\s+.*$)',
        "bold":        r'(\*\*[^*]+?\*\*|__[^_]+?__)',
        "italic":      r'(?<!\*)(\*[^*]+?\*)(?!\*)|(?<!_)(_[^_]+?_)(?!_)',
        "code_block":  r'(```[\s\S]*?```)',
        "inline_code": r'(`[^`]+?`)',
        "links":       r'(\[[^\]]+?\]\([^\)]+?\))',
        "lists":       r'(^\s*[\-\*\+]\s+)',
        "numbers":     r'(^\s*\d+\.\s+)',
    },
    "YAML": {
        "keys":     r'^(\s*[\w\-\.]+)\s*:',
        "strings":  r'(\".*?\"|\'.*?\')',
        "comments": r'(#.*?$)',
        "numbers":  r'\b(\d+\.?\d*)\b',
        "keywords": r'\b(true|false|yes|no|null|True|False|Yes|No|Null|TRUE|FALSE|YES|NO|NULL)\b',
    },
    "TOML": {
        "sections":  r'(^\s*\[{1,2}[^\]]+\]{1,2})',
        "keys":      r'^(\s*[\w\-\.]+)\s*=',
        "strings":   r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'|\".*?\"|\'.*?\')',
        "comments":  r'(#.*?$)',
        "numbers":   r'\b(\d+\.?\d*)\b',
        "keywords":  r'\b(true|false)\b',
    },
    "Plain Text": {},
}

# Map file extensions → language
EXT_MAP: Dict[str, str] = {
    ".py": "Python", ".pyw": "Python",
    ".cpp": "C++", ".cxx": "C++", ".cc": "C++", ".h": "C++", ".hpp": "C++",
    ".c": "C++",
    ".js": "JavaScript", ".mjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "JavaScript", ".tsx": "JavaScript",
    ".html": "HTML", ".htm": "HTML", ".xml": "HTML", ".svg": "HTML",
    ".css": "CSS", ".scss": "CSS", ".less": "CSS",
    ".json": "JSON",
    ".sql": "SQL",
    ".md": "Markdown", ".markdown": "Markdown",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
}

# ─── Theme colour palettes ──────────────────────────────────────────────
THEMES: Dict[str, Dict[str, Any]] = {
    "Dark": {
        "bg": "#1E1E1E", "fg": "#D4D4D4", "caret": "#AEAFAD",
        "select_bg": "#264F78", "select_fg": "#FFFFFF",
        "line_bg": "#1E1E1E", "line_fg": "#858585",
        "menu_bg": "#2D2D2D", "menu_fg": "#CCCCCC",
        "tab_bg": "#2D2D2D", "tab_fg": "#CCCCCC",
        "tab_sel_bg": "#1E1E1E", "tab_sel_fg": "#FFFFFF",
        "status_bg": "#007ACC", "status_fg": "#FFFFFF",
        "syntax": {
            "keywords":    "#569CD6",  "builtins":    "#DCDCAA",
            "strings":     "#CE9178",  "comments":    "#6A9955",
            "numbers":     "#B5CEA8",  "decorators":  "#DCDCAA",
            "tags":        "#569CD6",  "attrs":       "#9CDCFE",
            "selectors":   "#D7BA7D",  "properties":  "#9CDCFE",
            "keys":        "#9CDCFE",  "preprocessor":"#C586C0",
            "headings":    "#569CD6",  "bold":        "#FFFFFF",
            "italic":      "#CE9178",  "code_block":  "#D7BA7D",
            "inline_code": "#D7BA7D",  "links":       "#4EC9B0",
            "lists":       "#569CD6",  "sections":    "#DCDCAA",
        },
    },
    "Light": {
        "bg": "#FFFFFF", "fg": "#000000", "caret": "#000000",
        "select_bg": "#ADD6FF", "select_fg": "#000000",
        "line_bg": "#F3F3F3", "line_fg": "#237893",
        "menu_bg": "#F3F3F3", "menu_fg": "#000000",
        "tab_bg": "#ECECEC", "tab_fg": "#333333",
        "tab_sel_bg": "#FFFFFF", "tab_sel_fg": "#000000",
        "status_bg": "#007ACC", "status_fg": "#FFFFFF",
        "syntax": {
            "keywords":    "#0000FF",  "builtins":    "#795E26",
            "strings":     "#A31515",  "comments":    "#008000",
            "numbers":     "#098658",  "decorators":  "#795E26",
            "tags":        "#800000",  "attrs":       "#FF0000",
            "selectors":   "#800000",  "properties":  "#FF0000",
            "keys":        "#0451A5",  "preprocessor":"#AF00DB",
            "headings":    "#0000FF",  "bold":        "#000000",
            "italic":      "#A31515",  "code_block":  "#795E26",
            "inline_code": "#795E26",  "links":       "#006060",
            "lists":       "#0000FF",  "sections":    "#795E26",
        },
    },
}


class LineNumbers(tk.Canvas):
    """A canvas widget that draws line numbers alongside a Text widget."""

    def __init__(self, master: Any, text_widget: Optional[tk.Text] = None, **kw: Any) -> None:
        super().__init__(master, **kw)
        self.text_widget: Optional[tk.Text] = text_widget

    def redraw(self, theme: Dict[str, Any]) -> None:
        self.delete("all")
        self.configure(bg=theme["line_bg"])
        if self.text_widget is None:
            return
        tw = self.text_widget
        i = tw.index("@0,0")
        while True:
            dline = tw.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                self.winfo_width() - 8, y,
                anchor="ne", text=linenum,
                fill=theme["line_fg"],
                font=tw["font"],
            )
            i = tw.index(f"{i}+1line")
            if float(i) > float(tw.index("end")):
                break


class EditorTab:
    """Data container for one editor tab."""

    def __init__(
        self,
        frame: tk.Frame,
        text: tk.Text,
        line_nums: "LineNumbers",
        filepath: Optional[str] = None,
        language: str = "Plain Text",
    ) -> None:
        self.frame: tk.Frame = frame
        self.text: tk.Text = text
        self.line_nums: LineNumbers = line_nums
        self.filepath: Optional[str] = filepath
        self.language: str = language
        self.modified: bool = False
        self.encoding: str = "UTF-8"


class PhilNotepadPlus:
    """Main application class."""

    # ── construction ────────────────────────────────────────────────────
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("Phil Notepad+")
        self.root.geometry("1100x720")

        self.tabs: List[EditorTab] = []
        self.current_tab: Optional[EditorTab] = None
        self.theme_name: str = "Dark"
        self.theme: Dict[str, Any] = THEMES[self.theme_name]
        self.base_font_size: int = 11
        self.font_size: int = self.base_font_size
        self.font_family: str = "Consolas"
        self.word_wrap: bool = False
        self.recent_files: List[str] = []

        self._build_menu()
        self._build_notebook()
        self._build_status_bar()
        self._bind_shortcuts()
        self.root.after(0, self._enable_file_drag_drop)

        # Restore session or show welcome tab
        restored = self._load_session()
        if not restored:
            self._apply_theme()
            self._new_tab(
                title="Welcome",
                content=(
                    "╔══════════════════════════════════════════════╗\n"
                    "║          Welcome to Phil Notepad+            ║\n"
                    "╚══════════════════════════════════════════════╝\n\n"
                    "  A lightweight, Notepad++-style editor.\n\n"
                    "  Keyboard shortcuts\n"
                    "  ──────────────────────────────────────\n"
                    "  Ctrl+N        New file\n"
                    "  Ctrl+O        Open file\n"
                    "  Ctrl+S        Save\n"
                    "  Ctrl+Shift+S  Save As\n"
                    "  Ctrl+W        Close tab\n"
                    "  Ctrl+F        Find\n"
                    "  Ctrl+H        Find & Replace\n"
                    "  Ctrl+G        Go to line\n"
                    "  Ctrl+D        Duplicate line\n"
                    "  Ctrl+Tab      Next tab\n"
                    "  Ctrl++        Zoom in\n"
                    "  Ctrl+-        Zoom out\n"
                    "  Ctrl+0        Reset zoom\n\n"
                    "  Supported languages\n"
                    "  ──────────────────────────────────────\n"
                    "  Python · C++ · JavaScript · HTML · CSS\n"
                    "  JSON · SQL · Markdown · YAML · TOML\n"
                    "  Plain Text\n"
                    "\n"
                    "  Tip: Drag and drop one or more files onto the window to open them instantly.\n"
                ),
            )
        else:
            self._apply_theme()

        # Override window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── session persistence ─────────────────────────────────────────────
    def _save_session(self) -> None:
        """Save session state to .tmp file."""
        try:
            open_tabs: List[Dict[str, Any]] = []
            active_idx: int = 0
            for i, tab in enumerate(self.tabs):
                if tab.filepath and os.path.exists(tab.filepath):
                    try:
                        cursor = tab.text.index(tk.INSERT)
                    except Exception:
                        cursor = "1.0"
                    try:
                        scroll = tab.text.yview()
                        scroll_pos = scroll[0] if scroll else 0.0
                    except Exception:
                        scroll_pos = 0.0
                    open_tabs.append({
                        "filepath": tab.filepath,
                        "language": tab.language,
                        "cursor": cursor,
                        "scroll": scroll_pos,
                    })
            if self.current_tab:
                try:
                    active_idx = self.notebook.index(self.current_tab.frame)
                except Exception:
                    active_idx = 0

            session: Dict[str, Any] = {
                "recent_files": self.recent_files[:20],
                "open_tabs": open_tabs,
                "active_tab_index": active_idx,
                "window_geometry": self.root.geometry(),
                "theme_name": self.theme_name,
                "font_size": self.font_size,
                "word_wrap": self.word_wrap,
                "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Never crash on session save

    def _load_session(self) -> bool:
        """Load session state from .tmp file.  Returns True if tabs were restored."""
        if not os.path.exists(_SESSION_FILE):
            return False
        try:
            with open(_SESSION_FILE, "r", encoding="utf-8") as f:
                session: Dict[str, Any] = json.load(f)
        except Exception:
            return False

        # Restore settings
        try:
            geo = session.get("window_geometry", "")
            if geo:
                self.root.geometry(geo)
            self.theme_name = session.get("theme_name", "Dark")
            self.theme = THEMES.get(self.theme_name, THEMES["Dark"])
            self.font_size = session.get("font_size", self.base_font_size)
            self.word_wrap = session.get("word_wrap", False)
            self.recent_files = session.get("recent_files", [])
            self._rebuild_recent_menu()
        except Exception:
            pass

        # Restore tabs
        open_tabs: List[Dict[str, Any]] = session.get("open_tabs", [])
        restored_count: int = 0
        for tab_info in open_tabs:
            fp: str = tab_info.get("filepath", "")
            if not fp or not os.path.exists(fp):
                continue
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(fp, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception:
                    continue
            except Exception:
                continue

            lang: str = tab_info.get("language", "Plain Text")
            title: str = os.path.basename(fp)
            self._new_tab(title=title, content=content, filepath=fp, language=lang)
            restored_count += 1

            # Restore cursor and scroll
            try:
                cursor: str = tab_info.get("cursor", "1.0")
                self.current_tab.text.mark_set(tk.INSERT, cursor)  # type: ignore[union-attr]
                self.current_tab.text.see(cursor)  # type: ignore[union-attr]
            except Exception:
                pass
            try:
                scroll_pos: float = tab_info.get("scroll", 0.0)
                self.current_tab.text.yview_moveto(scroll_pos)  # type: ignore[union-attr]
            except Exception:
                pass

        if restored_count == 0:
            return False

        # Restore active tab
        try:
            active_idx: int = session.get("active_tab_index", 0)
            if 0 <= active_idx < len(self.tabs):
                self.notebook.select(self.tabs[active_idx].frame)
        except Exception:
            pass

        return True

    def _rebuild_recent_menu(self) -> None:
        """Rebuild the recent files submenu from self.recent_files."""
        try:
            self.recent_menu.delete(0, "end")
            for p in self.recent_files:
                self.recent_menu.add_command(
                    label=p, command=lambda pp=p: self._open_recent(pp)
                )
        except Exception:
            pass

    def _on_close(self) -> None:
        """Handle window close: save session then exit."""
        self._save_session()
        self.root.destroy()

    # ── menu bar ────────────────────────────────────────────────────────
    def _build_menu(self) -> None:
        self.menubar: tk.Menu = tk.Menu(self.root, tearoff=0)

        # File
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New              Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open…            Ctrl+O", command=self._open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save             Ctrl+S", command=self._save_file)
        file_menu.add_command(label="Save As…  Ctrl+Shift+S", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab        Ctrl+W", command=self._close_tab)
        file_menu.add_separator()
        self.recent_menu: tk.Menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Edit
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo             Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo             Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut              Ctrl+X", command=self._cut)
        edit_menu.add_command(label="Copy             Ctrl+C", command=self._copy)
        edit_menu.add_command(label="Paste            Ctrl+V", command=self._paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All       Ctrl+A", command=self._select_all)
        edit_menu.add_command(label="Duplicate Line   Ctrl+D", command=self._duplicate_line)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        # Search
        search_menu = tk.Menu(self.menubar, tearoff=0)
        search_menu.add_command(label="Find…            Ctrl+F", command=self._open_find)
        search_menu.add_command(label="Replace…         Ctrl+H", command=self._open_replace)
        search_menu.add_separator()
        search_menu.add_command(label="Go to Line…      Ctrl+G", command=self._go_to_line)
        self.menubar.add_cascade(label="Search", menu=search_menu)

        # View
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_command(label="Zoom In          Ctrl++", command=self._zoom_in)
        view_menu.add_command(label="Zoom Out         Ctrl+-", command=self._zoom_out)
        view_menu.add_command(label="Reset Zoom       Ctrl+0", command=self._zoom_reset)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Word Wrap", command=self._toggle_word_wrap)
        view_menu.add_separator()
        self.theme_menu: tk.Menu = tk.Menu(view_menu, tearoff=0)
        self.theme_menu.add_command(label="Dark", command=lambda: self._set_theme("Dark"))
        self.theme_menu.add_command(label="Light", command=lambda: self._set_theme("Light"))
        view_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Language
        lang_menu = tk.Menu(self.menubar, tearoff=0)
        for lang in SYNTAX:
            lang_menu.add_command(label=lang, command=lambda l=lang: self._set_language(l))
        self.menubar.add_cascade(label="Language", menu=lang_menu)

        # Help
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)

    # ── notebook (tabs area) ────────────────────────────────────────────
    def _build_notebook(self) -> None:
        style = ttk.Style()
        style.theme_use("default")
        self.notebook: ttk.Notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── status bar ──────────────────────────────────────────────────────
    def _build_status_bar(self) -> None:
        self.status_frame: tk.Frame = tk.Frame(self.root, height=24)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_left: tk.Label = tk.Label(self.status_frame, anchor="w", padx=10)
        self.status_left.pack(side="left", fill="x", expand=True)
        self.status_right: tk.Label = tk.Label(self.status_frame, anchor="e", padx=10)
        self.status_right.pack(side="right")

    def _update_status(self, event: Any = None) -> None:
        tab = self.current_tab
        if not tab:
            return
        try:
            pos = tab.text.index(tk.INSERT)
            line, col = pos.split(".")
            total = int(tab.text.index("end-1c").split(".")[0])
            self.status_left.config(
                text=f"  Ln {line}, Col {int(col)+1}    |    Lines: {total}    |    {tab.language}"
            )
            self.status_right.config(text=f"{tab.encoding}    Zoom: {self.font_size}pt  ")
        except Exception:
            pass

    # ── keybindings ─────────────────────────────────────────────────────
    def _bind_shortcuts(self) -> None:
        r = self.root
        r.bind("<Control-n>", lambda e: self._new_file())
        r.bind("<Control-N>", lambda e: self._new_file())
        r.bind("<Control-o>", lambda e: self._open_file())
        r.bind("<Control-O>", lambda e: self._open_file())
        r.bind("<Control-s>", lambda e: self._save_file())
        r.bind("<Control-S>", lambda e: self._save_file())
        r.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        r.bind("<Control-w>", lambda e: self._close_tab())
        r.bind("<Control-W>", lambda e: self._close_tab())
        r.bind("<Control-f>", lambda e: self._open_find())
        r.bind("<Control-F>", lambda e: self._open_find())
        r.bind("<Control-h>", lambda e: self._open_replace())
        r.bind("<Control-H>", lambda e: self._open_replace())
        r.bind("<Control-g>", lambda e: self._go_to_line())
        r.bind("<Control-G>", lambda e: self._go_to_line())
        r.bind("<Control-d>", lambda e: self._duplicate_line())
        r.bind("<Control-D>", lambda e: self._duplicate_line())
        r.bind("<Control-Tab>", lambda e: self._next_tab())
        r.bind("<Control-plus>", lambda e: self._zoom_in())
        r.bind("<Control-equal>", lambda e: self._zoom_in())
        r.bind("<Control-minus>", lambda e: self._zoom_out())
        r.bind("<Control-0>", lambda e: self._zoom_reset())

    def _enable_file_drag_drop(self) -> None:
        """Enable Windows file drag-and-drop for the main window."""
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            shell32 = ctypes.windll.shell32
            ole32 = ctypes.windll.ole32
            ole32.OleInitialize(None)

            shell32.DragQueryFileW.restype = ctypes.c_uint
            shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
            shell32.DragFinish.restype = None
            shell32.DragFinish.argtypes = [wintypes.HANDLE]
            shell32.DragAcceptFiles.restype = wintypes.BOOL
            shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]

            hwnd = self.root.winfo_id()
            GWL_WNDPROC = -4
            WM_DROPFILES = 0x0233

            user32.GetWindowLongPtrW.restype = ctypes.c_void_p
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.SetWindowLongPtrW.restype = ctypes.c_void_p
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
            LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

            WNDPROC = ctypes.WINFUNCTYPE(
                LRESULT,
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            )

            def _window_proc(hWnd: wintypes.HWND, msg: wintypes.UINT, wParam: wintypes.WPARAM, lParam: wintypes.LPARAM):
                if msg == WM_DROPFILES:
                    self._handle_drop_files(wintypes.HANDLE(int(wParam)))
                    return 0
                return self._original_wndproc(hWnd, msg, wParam, lParam)

            self._window_proc = WNDPROC(_window_proc)
            self._original_wndproc = ctypes.cast(
                user32.GetWindowLongPtrW(hwnd, GWL_WNDPROC),
                WNDPROC,
            )
            user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, ctypes.cast(self._window_proc, ctypes.c_void_p))
            shell32.DragAcceptFiles(hwnd, True)
        except Exception:
            pass

    def _handle_drop_files(self, hdrop: wintypes.HANDLE) -> None:
        """Open files that are dropped onto the app window."""
        shell32 = ctypes.windll.shell32
        count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
        for idx in range(count):
            length = shell32.DragQueryFileW(hdrop, idx, None, 0)
            buffer = ctypes.create_unicode_buffer(length + 1)
            shell32.DragQueryFileW(hdrop, idx, buffer, length + 1)
            path = buffer.value
            if os.path.isfile(path):
                self._open_dropped_file(path)
        shell32.DragFinish(hdrop)

    def _open_dropped_file(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as exc:
            messagebox.showerror("Open File", f"Unable to open dropped file:\n{path}\n\n{exc}")
            return

        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Plain Text")
        self._new_tab(title=os.path.basename(path), content=content, filepath=path, language=lang)
        self._add_recent(path)

    # ── tab helpers ─────────────────────────────────────────────────────
    def _make_editor(self, parent: tk.Frame) -> Tuple[tk.Text, LineNumbers]:
        """Create a text widget + line-number canvas inside *parent* frame."""
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        t = self.theme
        fnt = (self.font_family, self.font_size)
        wrap = "word" if self.word_wrap else "none"

        line_nums = LineNumbers(frame, text_widget=None, width=50, highlightthickness=0, bd=0)
        line_nums.pack(side="left", fill="y")

        text = tk.Text(
            frame, font=fnt, wrap=wrap, undo=True,
            bg=t["bg"], fg=t["fg"],
            insertbackground=t["caret"],
            selectbackground=t["select_bg"],
            selectforeground=t["select_fg"],
            borderwidth=0, padx=6, pady=4,
            tabs=("4c",),
        )
        text.pack(side="left", fill="both", expand=True)

        # Scrollbars
        vscroll = tk.Scrollbar(frame, orient="vertical", command=text.yview)
        vscroll.pack(side="right", fill="y")
        text.config(yscrollcommand=vscroll.set)

        if not self.word_wrap:
            hscroll = tk.Scrollbar(parent, orient="horizontal", command=text.xview)
            hscroll.pack(side="bottom", fill="x")
            text.config(xscrollcommand=hscroll.set)

        line_nums.text_widget = text

        # Events
        text.bind("<KeyRelease>", self._on_key_release)
        text.bind("<ButtonRelease-1>", self._on_key_release)
        text.bind("<MouseWheel>", self._on_scroll)
        text.bind("<Configure>", lambda e: self._redraw_line_numbers())
        text.bind("<Button-3>", self._context_menu)

        return text, line_nums

    def _new_tab(
        self,
        title: str = "Untitled",
        content: str = "",
        filepath: Optional[str] = None,
        language: str = "Plain Text",
    ) -> None:
        outer = tk.Frame(self.notebook)
        text, line_nums = self._make_editor(outer)
        if content:
            text.insert("1.0", content)
        tab = EditorTab(outer, text, line_nums, filepath, language)
        self.tabs.append(tab)
        self.notebook.add(outer, text=f"  {title}  ")
        self.notebook.select(outer)
        self.current_tab = tab
        text.edit_modified(False)
        self._highlight_syntax()
        self._redraw_line_numbers()
        self._update_status()

    def _get_tab_for_frame(self, frame: Any) -> Optional[EditorTab]:
        for tab in self.tabs:
            if tab.frame is frame:
                return tab
        return None

    def _on_tab_changed(self, event: Any = None) -> None:
        sel = self.notebook.select()
        if not sel:
            self.current_tab = None
            return
        widget = self.root.nametowidget(sel)
        tab = self._get_tab_for_frame(widget)
        self.current_tab = tab
        if tab:
            self._highlight_syntax()
            self._redraw_line_numbers()
            self._update_status()

    # ── file operations ─────────────────────────────────────────────────
    def _new_file(self) -> None:
        self._new_tab()

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[
            ("All Files", "*.*"),
            ("Python", "*.py *.pyw"),
            ("C++", "*.cpp *.cxx *.cc *.h *.hpp *.c"),
            ("JavaScript", "*.js *.mjs *.jsx *.ts *.tsx"),
            ("HTML", "*.html *.htm"),
            ("CSS", "*.css *.scss *.less"),
            ("JSON", "*.json"),
            ("SQL", "*.sql"),
            ("Markdown", "*.md *.markdown"),
            ("YAML", "*.yaml *.yml"),
            ("TOML", "*.toml"),
            ("Text", "*.txt"),
        ])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Plain Text")
        title = os.path.basename(path)
        self._new_tab(title=title, content=content, filepath=path, language=lang)
        self._add_recent(path)

    def _save_file(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        if tab.filepath:
            self._write_file(tab, tab.filepath)
        else:
            self._save_file_as()
        self._save_session()

    def _save_file_as(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[
            ("All Files", "*.*"),
            ("Python", "*.py"), ("C++", "*.cpp"),
            ("JavaScript", "*.js"),
            ("HTML", "*.html"), ("CSS", "*.css"),
            ("JSON", "*.json"), ("SQL", "*.sql"),
            ("Markdown", "*.md"), ("YAML", "*.yaml"),
            ("TOML", "*.toml"), ("Text", "*.txt"),
        ])
        if not path:
            return
        self._write_file(tab, path)
        tab.filepath = path
        ext = os.path.splitext(path)[1].lower()
        tab.language = EXT_MAP.get(ext, "Plain Text")
        idx = self.notebook.index(tab.frame)
        self.notebook.tab(idx, text=f"  {os.path.basename(path)}  ")
        self._highlight_syntax()
        self._update_status()
        self._add_recent(path)
        self._save_session()

    def _write_file(self, tab: EditorTab, path: str) -> None:
        content = tab.text.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        tab.modified = False
        tab.text.edit_modified(False)
        idx = self.notebook.index(tab.frame)
        title = os.path.basename(path) if path else "Untitled"
        self.notebook.tab(idx, text=f"  {title}  ")

    def _close_tab(self) -> None:
        if not self.tabs:
            return
        tab = self.current_tab
        if not tab:
            return
        if tab.text.edit_modified():
            ans = messagebox.askyesnocancel("Save?", "Do you want to save changes before closing?")
            if ans is None:
                return
            if ans:
                self._save_file()
        idx = self.notebook.index(tab.frame)
        self.notebook.forget(idx)
        self.tabs.remove(tab)
        if self.tabs:
            self.notebook.select(self.tabs[-1].frame)
        else:
            self.current_tab = None
        self._save_session()

    def _add_recent(self, path: str) -> None:
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:20]
        self._rebuild_recent_menu()

    def _open_recent(self, path: str) -> None:
        if not os.path.exists(path):
            messagebox.showerror("Error", f"File not found:\n{path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Plain Text")
        self._new_tab(title=os.path.basename(path), content=content, filepath=path, language=lang)

    # ── edit helpers ────────────────────────────────────────────────────
    def _undo(self) -> None:
        tab = self.current_tab
        if tab:
            try:
                tab.text.edit_undo()
            except tk.TclError:
                pass

    def _redo(self) -> None:
        tab = self.current_tab
        if tab:
            try:
                tab.text.edit_redo()
            except tk.TclError:
                pass

    def _cut(self) -> None:
        tab = self.current_tab
        if tab:
            tab.text.event_generate("<<Cut>>")

    def _copy(self) -> None:
        tab = self.current_tab
        if tab:
            tab.text.event_generate("<<Copy>>")

    def _paste(self) -> None:
        tab = self.current_tab
        if tab:
            tab.text.event_generate("<<Paste>>")

    def _select_all(self) -> None:
        tab = self.current_tab
        if tab:
            tab.text.tag_add("sel", "1.0", "end")

    def _duplicate_line(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        t = tab.text
        line = t.get("insert linestart", "insert lineend")
        t.insert("insert lineend", "\n" + line)

    # ── search helpers ──────────────────────────────────────────────────
    def _open_find(self) -> None:
        self._find_replace_dialog(replace=False)

    def _open_replace(self) -> None:
        self._find_replace_dialog(replace=True)

    def _find_replace_dialog(self, replace: bool = False) -> None:
        tab = self.current_tab
        if not tab:
            return
        win = tk.Toplevel(self.root)
        win.title("Find & Replace" if replace else "Find")
        win.geometry("420x180" if replace else "420x130")
        win.resizable(False, False)
        win.transient(self.root)

        tk.Label(win, text="Find:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        find_var = tk.StringVar()
        tk.Entry(win, textvariable=find_var, width=32).grid(row=0, column=1, padx=4, pady=6)

        repl_var = tk.StringVar()
        if replace:
            tk.Label(win, text="Replace:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
            tk.Entry(win, textvariable=repl_var, width=32).grid(row=1, column=1, padx=4, pady=6)

        case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="Case sensitive", variable=case_var).grid(
            row=(2 if replace else 1), column=1, sticky="w", padx=4
        )

        btn_row = 3 if replace else 2
        btn_frame = tk.Frame(win)
        btn_frame.grid(row=btn_row, column=0, columnspan=2, pady=8)

        def _find() -> None:
            tab.text.tag_remove("found", "1.0", "end")
            query = find_var.get()
            if not query:
                return
            nocase = not case_var.get()
            idx = "1.0"
            count_var = tk.IntVar()
            while True:
                idx = tab.text.search(query, idx, stopindex="end", nocase=nocase, count=count_var)
                if not idx:
                    break
                end = f"{idx}+{count_var.get()}c"
                tab.text.tag_add("found", idx, end)
                idx = end
            tab.text.tag_config("found", background="#FFD700", foreground="#000000")

        def _replace_next() -> None:
            query = find_var.get()
            replacement = repl_var.get()
            if not query:
                return
            nocase = not case_var.get()
            idx = tab.text.search(query, "insert", stopindex="end", nocase=nocase)
            if idx:
                end = f"{idx}+{len(query)}c"
                tab.text.delete(idx, end)
                tab.text.insert(idx, replacement)
                self._highlight_syntax()

        def _replace_all() -> None:
            query = find_var.get()
            replacement = repl_var.get()
            if not query:
                return
            content = tab.text.get("1.0", "end-1c")
            if case_var.get():
                new_content = content.replace(query, replacement)
            else:
                new_content = re.sub(re.escape(query), replacement, content, flags=re.IGNORECASE)
            tab.text.delete("1.0", "end")
            tab.text.insert("1.0", new_content)
            self._highlight_syntax()

        tk.Button(btn_frame, text="Find All", command=_find, width=10).pack(side="left", padx=4)
        if replace:
            tk.Button(btn_frame, text="Replace", command=_replace_next, width=10).pack(side="left", padx=4)
            tk.Button(btn_frame, text="Replace All", command=_replace_all, width=10).pack(side="left", padx=4)

    def _go_to_line(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        total = int(tab.text.index("end-1c").split(".")[0])
        line = simpledialog.askinteger("Go to Line", f"Line number (1-{total}):", minvalue=1, maxvalue=total)
        if line:
            tab.text.mark_set("insert", f"{line}.0")
            tab.text.see(f"{line}.0")
            self._update_status()

    # ── zoom ────────────────────────────────────────────────────────────
    def _zoom_in(self) -> None:
        self.font_size = min(self.font_size + 1, 40)
        self._apply_font()

    def _zoom_out(self) -> None:
        self.font_size = max(self.font_size - 1, 6)
        self._apply_font()

    def _zoom_reset(self) -> None:
        self.font_size = self.base_font_size
        self._apply_font()

    def _apply_font(self) -> None:
        fnt = (self.font_family, self.font_size)
        for tab in self.tabs:
            tab.text.config(font=fnt)
        self._redraw_line_numbers()
        self._update_status()

    # ── word wrap ───────────────────────────────────────────────────────
    def _toggle_word_wrap(self) -> None:
        self.word_wrap = not self.word_wrap
        wrap = "word" if self.word_wrap else "none"
        for tab in self.tabs:
            tab.text.config(wrap=wrap)
        self._redraw_line_numbers()

    # ── language ────────────────────────────────────────────────────────
    def _set_language(self, lang: str) -> None:
        tab = self.current_tab
        if not tab:
            return
        tab.language = lang
        self._highlight_syntax()
        self._update_status()

    # ── syntax highlighting ─────────────────────────────────────────────
    def _highlight_syntax(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        text = tab.text
        lang = tab.language
        rules = SYNTAX.get(lang, {})
        colors: Dict[str, str] = self.theme["syntax"]

        # Remove existing tags
        for tag_name in colors:
            text.tag_remove(tag_name, "1.0", "end")

        content = text.get("1.0", "end-1c")
        if not content.strip() or not rules:
            return

        for tag_name, pattern in rules.items():
            color = colors.get(tag_name)
            if not color:
                continue
            text.tag_configure(tag_name, foreground=color)
            try:
                for m in re.finditer(pattern, content, re.MULTILINE):
                    start_idx = m.start(1) if m.lastindex else m.start()
                    end_idx = m.end(1) if m.lastindex else m.end()
                    start = f"1.0+{start_idx}c"
                    end = f"1.0+{end_idx}c"
                    text.tag_add(tag_name, start, end)
            except re.error:
                pass

        # comments & strings should override other highlighting
        for override in ("comments", "strings", "code_block"):
            if override in rules:
                text.tag_raise(override)

    # ── line numbers ────────────────────────────────────────────────────
    def _redraw_line_numbers(self) -> None:
        tab = self.current_tab
        if tab:
            tab.line_nums.redraw(self.theme)

    # ── event handlers ──────────────────────────────────────────────────
    def _on_key_release(self, event: Any = None) -> None:
        tab = self.current_tab
        if not tab:
            return
        # Modified indicator
        if tab.text.edit_modified():
            if not tab.modified:
                tab.modified = True
                idx = self.notebook.index(tab.frame)
                title = self.notebook.tab(idx, "text").strip()
                if not title.startswith("*"):
                    self.notebook.tab(idx, text=f" *{title} ")
        self._highlight_syntax()
        self._redraw_line_numbers()
        self._update_status()

    def _on_scroll(self, event: Any = None) -> None:
        self.root.after(10, self._redraw_line_numbers)

    # ── context menu ────────────────────────────────────────────────────
    def _context_menu(self, event: Any) -> None:
        tab = self.current_tab
        if not tab:
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cut", command=self._cut)
        menu.add_command(label="Copy", command=self._copy)
        menu.add_command(label="Paste", command=self._paste)
        menu.add_separator()
        menu.add_command(label="Select All", command=self._select_all)
        menu.add_command(label="Delete", command=lambda: tab.text.delete("sel.first", "sel.last"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ── theme ───────────────────────────────────────────────────────────
    def _set_theme(self, name: str) -> None:
        self.theme_name = name
        self.theme = THEMES[name]
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self.theme
        style = ttk.Style()
        style.configure("TNotebook", background=t["tab_bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=t["tab_bg"], foreground=t["tab_fg"],
            padding=[12, 4],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", t["tab_sel_bg"])],
            foreground=[("selected", t["tab_sel_fg"])],
        )
        self.status_frame.config(bg=t["status_bg"])
        self.status_left.config(bg=t["status_bg"], fg=t["status_fg"])
        self.status_right.config(bg=t["status_bg"], fg=t["status_fg"])
        self.root.config(bg=t["bg"])

        for tab in self.tabs:
            tab.text.config(
                bg=t["bg"], fg=t["fg"],
                insertbackground=t["caret"],
                selectbackground=t["select_bg"],
                selectforeground=t["select_fg"],
            )
            tab.line_nums.config(bg=t["line_bg"])
        self._highlight_syntax()
        self._redraw_line_numbers()

    # ── next tab ────────────────────────────────────────────────────────
    def _next_tab(self) -> None:
        if len(self.tabs) < 2:
            return
        idx = self.notebook.index(self.notebook.select())
        nxt = (idx + 1) % len(self.tabs)
        self.notebook.select(self.tabs[nxt].frame)

    # ── about ───────────────────────────────────────────────────────────
    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Phil Notepad+",
            "Phil Notepad+\n"
            "Version 1.2\n\n"
            "A Notepad++-style text editor\n"
            "built with Python & tkinter.\n\n"
            "Supported: Python, C++, JavaScript,\n"
            "HTML, CSS, JSON, SQL, Markdown,\n"
            "YAML, TOML, Plain Text\n\n"
            "Session auto-saved to .tmp\n\n"
            "© 2026",
        )


# ─── Entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = PhilNotepadPlus(root)
    root.mainloop()
