#!/usr/bin/env python3
"""
Notepad-- — A Notepad++-like text editor built with Python / tkinter.
Features: tabbed editing, syntax highlighting, line numbers, find & replace,
dark/light themes, zoom, word-wrap toggle, go-to-line, recent files,
session persistence (.tmp), and more.
"""

import json
import os
import re
import sys
import ctypes
import csv
import difflib
import tempfile
import textwrap
import webbrowser
from ctypes import wintypes
from html import escape as html_escape, unescape as html_unescape
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser, font as tkfont
from typing import Any, Dict, List, Optional, Tuple

# ─── Determine base directory (works for both script and frozen exe) ───
if getattr(sys, "frozen", False):
    _BASE_DIR: str = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_SESSION_FILE: str = os.path.join(_BASE_DIR, "phil_notepad_plus.tmp")
_HISTORY_FILE: str = os.path.join(_BASE_DIR, "phil_notepad_plus_history.tmp")

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
        "keywords": r"(?i)\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|"
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

TEXT_FILE_EXTENSIONS = set(EXT_MAP) | {
    ".txt", ".text", ".log",
    ".csv", ".tsv", ".srt",
    ".ini", ".cfg", ".conf",
    ".bat", ".cmd", ".ps1", ".sh",
}

DEFAULT_FONT_CANDIDATES: Tuple[str, ...] = (
    "D2Coding",
    "D2Coding ligature",
    "NanumGothicCoding",
    "Malgun Gothic",
    "Cascadia Mono",
    "Consolas",
    "Courier New",
)

LATIN_ONLY_FONT_FALLBACKS: Tuple[str, ...] = (
    "Cascadia Mono",
    "Consolas",
    "Courier New",
)

A4_SIZE_MM: Tuple[int, int] = (210, 297)
PRINT_MARGIN_MM: int = 15
DEFAULT_TAB_SIZE: int = 4
DEFAULT_OCCURRENCE_COLOR: str = "#7A5C00"
DEFAULT_OCCURRENCE_CURRENT_COLOR: str = "#FFB900"
APP_NAME: str = "Notepad--"

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
            "keywords":    "#82AAFF",  "builtins":    "#FFCB6B",
            "strings":     "#C3E88D",  "comments":    "#7F8C98",
            "numbers":     "#F78C6C",  "decorators":  "#C792EA",
            "tags":        "#F07178",  "attrs":       "#FFCB6B",
            "selectors":   "#C792EA",  "properties":  "#89DDFF",
            "keys":        "#82AAFF",  "preprocessor":"#FF5370",
            "headings":    "#89DDFF",  "bold":        "#EEFFFF",
            "italic":      "#F78C6C",  "code_block":  "#C792EA",
            "inline_code": "#FFCB6B",  "links":       "#80CBC4",
            "lists":       "#F07178",  "sections":    "#C3E88D",
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
            "keywords":    "#005CC5",  "builtins":    "#B08800",
            "strings":     "#22863A",  "comments":    "#6A737D",
            "numbers":     "#D73A49",  "decorators":  "#6F42C1",
            "tags":        "#D73A49",  "attrs":       "#E36209",
            "selectors":   "#6F42C1",  "properties":  "#005CC5",
            "keys":        "#032F62",  "preprocessor":"#B31D28",
            "headings":    "#005CC5",  "bold":        "#24292E",
            "italic":      "#D73A49",  "code_block":  "#6F42C1",
            "inline_code": "#B08800",  "links":       "#0086B3",
            "lists":       "#E36209",  "sections":    "#22863A",
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
        hscroll: Optional[tk.Scrollbar] = None,
        margin_guide: Optional[tk.Frame] = None,
        filepath: Optional[str] = None,
        language: str = "Plain Text",
        last_known_size: Optional[int] = None,
        last_known_mtime: Optional[float] = None,
        title: str = "new1",
    ) -> None:
        self.frame: tk.Frame = frame
        self.text: tk.Text = text
        self.line_nums: LineNumbers = line_nums
        self.hscroll: Optional[tk.Scrollbar] = hscroll
        self.margin_guide: Optional[tk.Frame] = margin_guide
        self.filepath: Optional[str] = filepath
        self.title: str = title
        self.language: str = language
        self.modified: bool = False
        self.encoding: str = "UTF-8"
        self.last_known_size: Optional[int] = last_known_size
        self.last_known_mtime: Optional[float] = last_known_mtime
        self.needs_reload: bool = False
        self.virtual_close_label: Optional[tk.Label] = None
        self.virtual_close_char: str = ""
        self.virtual_close_line: str = ""
        self.minimap: Optional[tk.Canvas] = None
        self.minimap_separator: Optional[tk.Frame] = None
        self.occurrence_query: str = ""
        self.occurrence_lines: List[int] = []


class NotepadMinusMinus:
    """Main application class."""

    # ── construction ────────────────────────────────────────────────────
    def __init__(self, root: tk.Tk, startup_paths: Optional[List[str]] = None) -> None:
        self.root: tk.Tk = root
        self.root.title(APP_NAME)
        self.root.geometry("1100x720")

        self.tabs: List[EditorTab] = []
        self.current_tab: Optional[EditorTab] = None
        self.theme_name: str = "Dark"
        self.theme: Dict[str, Any] = THEMES[self.theme_name]
        self.base_font_size: int = 11
        self.font_size: int = self.base_font_size
        self.font_family: str = self._preferred_font_family()
        self.word_wrap: bool = False
        self.tab_size: int = DEFAULT_TAB_SIZE
        self.show_a4_margin_guide: bool = True
        self.occurrence_color: str = DEFAULT_OCCURRENCE_COLOR
        self.occurrence_current_color: str = DEFAULT_OCCURRENCE_CURRENT_COLOR
        self.recent_files: List[str] = []
        self.file_history: Dict[str, Dict[str, Any]] = {}
        self._new_file_counter: int = 1
        self._syntax_highlight_job: Optional[str] = None
        self.markdown_view_visible: bool = False
        self.markdown_view_frame: Optional[tk.Frame] = None
        self.markdown_view_text: Optional[tk.Text] = None
        self.markdown_view_title: Optional[tk.Label] = None
        self.preview_mode: str = "markdown"

        self._build_menu()
        self._build_notebook()
        self._build_status_bar()
        self._bind_shortcuts()
        self._load_history()
        self.root.after(0, self._enable_file_drag_drop)

        startup_paths = self._normalize_startup_paths(startup_paths or [])

        # Restore session, open files passed by the OS/command line, or show welcome tab.
        restored = self._load_session()
        opened_startup_files = self._open_startup_files(startup_paths)
        if not restored and not opened_startup_files:
            self._apply_theme()
            self._new_tab(
                title="Welcome",
                content=self._welcome_content(),
            )
        else:
            self._apply_theme()

        # Override window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(2000, self._check_external_file_changes)

    # ── session persistence ─────────────────────────────────────────────
    def _save_session(self) -> None:
        """Save session state to .tmp file."""
        try:
            open_tabs: List[Dict[str, Any]] = []
            active_idx: int = 0
            for i, tab in enumerate(self.tabs):
                try:
                    cursor = tab.text.index(tk.INSERT)
                except Exception:
                    cursor = "1.0"
                try:
                    scroll = tab.text.yview()
                    scroll_pos = scroll[0] if scroll else 0.0
                except Exception:
                    scroll_pos = 0.0

                tab_info: Dict[str, Any] = {
                    "title": self._tab_title(tab),
                    "filepath": tab.filepath,
                    "content": tab.text.get("1.0", "end-1c"),
                    "language": tab.language,
                    "cursor": cursor,
                    "scroll": scroll_pos,
                    "modified": bool(tab.modified or tab.text.edit_modified()),
                    "last_known_size": tab.last_known_size,
                    "last_known_mtime": tab.last_known_mtime,
                }
                open_tabs.append(tab_info)
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
                "font_family": self.font_family,
                "font_size": self.font_size,
                "word_wrap": self.word_wrap,
                "tab_size": self.tab_size,
                "show_a4_margin_guide": self.show_a4_margin_guide,
                "occurrence_color": self.occurrence_color,
                "occurrence_current_color": self.occurrence_current_color,
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
            self.font_family = session.get("font_family", self.font_family)
            self.font_family = self._korean_safe_font_family(self.font_family)
            self.font_size = session.get("font_size", self.base_font_size)
            self.base_font_size = self.font_size
            self.word_wrap = session.get("word_wrap", False)
            self.tab_size = self._normalize_tab_size(session.get("tab_size", DEFAULT_TAB_SIZE))
            self.show_a4_margin_guide = session.get("show_a4_margin_guide", True)
            self.occurrence_color = self._normalize_color(
                session.get("occurrence_color", self.occurrence_color),
                DEFAULT_OCCURRENCE_COLOR,
            )
            self.occurrence_current_color = self._normalize_color(
                session.get("occurrence_current_color", self.occurrence_current_color),
                DEFAULT_OCCURRENCE_CURRENT_COLOR,
            )
            session_recent = session.get("recent_files", [])
            self.recent_files = self._merge_recent_files(self.recent_files, session_recent)
            self._rebuild_recent_menu()
        except Exception:
            pass

        # Restore tabs
        open_tabs: List[Dict[str, Any]] = session.get("open_tabs", [])
        restored_count: int = 0
        for tab_info in open_tabs:
            fp: str = tab_info.get("filepath", "")
            modified = bool(tab_info.get("modified", False))
            has_session_content = isinstance(tab_info.get("content"), str)
            if fp and modified and has_session_content:
                content = tab_info.get("content", "")
            elif fp:
                if not os.path.exists(fp):
                    continue
                try:
                    content = self._read_text_file(fp)
                except Exception:
                    continue
            else:
                content = tab_info.get("content", "")

            lang: str = tab_info.get("language", "Plain Text")
            title: str = os.path.basename(fp) if fp else self._session_new_title(tab_info.get("title", ""))
            size = tab_info.get("last_known_size")
            if fp and size is None:
                size = self._get_file_size(fp)
            mtime = tab_info.get("last_known_mtime")
            if fp and mtime is None:
                mtime = self._get_file_mtime(fp)
            if fp and not self._can_open_file_path(fp, show_message=False):
                continue
            self._new_tab(
                title=title,
                content=content,
                filepath=fp or None,
                language=lang,
                last_known_size=size,
                last_known_mtime=mtime,
                mark_modified=modified,
            )
            if fp:
                self._record_file_history(fp)
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
                    label=self._recent_menu_label(p), command=lambda pp=p: self._open_recent(pp)
                )
        except Exception:
            pass

    def _load_history(self) -> None:
        """Load durable file-open history independent of session restore."""
        if not os.path.exists(_HISTORY_FILE):
            self._rebuild_recent_menu()
            return
        try:
            with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                history: Dict[str, Any] = json.load(f)
        except Exception:
            self._rebuild_recent_menu()
            return

        files = history.get("files", {})
        if isinstance(files, dict):
            self.file_history = {
                path: info for path, info in files.items()
                if isinstance(path, str) and isinstance(info, dict)
            }

        recent = history.get("recent_files", [])
        if isinstance(recent, list):
            self.recent_files = [
                path for path in recent
                if isinstance(path, str) and path
            ][:20]
        self._rebuild_recent_menu()

    def _save_history(self) -> None:
        """Persist recent files and their last known sizes immediately."""
        try:
            history = {
                "recent_files": self.recent_files[:20],
                "files": self.file_history,
                "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _merge_recent_files(self, *groups: List[str]) -> List[str]:
        merged: List[str] = []
        for group in groups:
            for path in group:
                if isinstance(path, str) and path and path not in merged:
                    merged.append(path)
        return merged[:20]

    def _get_file_size(self, path: str) -> Optional[int]:
        try:
            return os.path.getsize(path)
        except OSError:
            return None

    def _get_file_mtime(self, path: str) -> Optional[float]:
        try:
            return os.path.getmtime(path)
        except OSError:
            return None

    def _format_file_size(self, size: Optional[int]) -> str:
        if size is None:
            return "size unknown"
        units = ("B", "KB", "MB", "GB", "TB")
        value = float(size)
        unit = units[0]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                break
            value /= 1024
        if unit == "B":
            return f"{int(value)} {unit}"
        return f"{value:.1f} {unit}"

    def _recent_menu_label(self, path: str) -> str:
        info = self.file_history.get(path, {})
        size = info.get("last_size")
        return f"{path}    [{self._format_file_size(size)}]"

    def _record_file_history(self, path: str) -> None:
        size = self._get_file_size(path)
        mtime = self._get_file_mtime(path)
        self.file_history[path] = {
            "last_size": size,
            "last_mtime": mtime,
            "last_opened": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        for tab in self.tabs:
            if tab.filepath == path:
                tab.last_known_size = size
                tab.last_known_mtime = mtime
                tab.needs_reload = False
                self._update_tab_title(tab)

    def _on_close(self) -> None:
        """Handle window close: save session then exit."""
        self._save_history()
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
        file_menu.add_command(label="Reload File", command=self._reload_current_file)
        file_menu.add_separator()
        file_menu.add_command(label="Print…           Ctrl+P", command=self._print_preview)
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
        edit_menu.add_command(label="Toggle Comment   Ctrl+/", command=self._toggle_comment)
        edit_menu.add_command(label="Insert Date/Time Ctrl+;", command=lambda: self._on_insert_datetime_shortcut(None))
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences…   Ctrl+,", command=self._open_preferences)
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
        view_menu.add_command(label="Toggle A4 Margin Guide", command=self._toggle_a4_margin_guide)
        view_menu.add_separator()
        view_menu.add_command(label="Markdown View    Ctrl+M", command=self._open_markdown_view)
        view_menu.add_command(label="HTML Preview", command=lambda: self._open_preview("html"))
        view_menu.add_command(label="CSV/TSV Preview", command=lambda: self._open_preview("table"))
        view_menu.add_command(label="JSON Tree Preview", command=lambda: self._open_preview("json"))
        view_menu.add_command(label="Outline Preview", command=lambda: self._open_preview("outline"))
        view_menu.add_command(label="Search Preview", command=lambda: self._open_preview("search"))
        view_menu.add_command(label="Diff Preview", command=lambda: self._open_preview("diff"))
        view_menu.add_separator()
        self.theme_menu: tk.Menu = tk.Menu(view_menu, tearoff=0)
        self.theme_menu.add_command(label="Dark", command=lambda: self._set_theme("Dark"))
        self.theme_menu.add_command(label="Light", command=lambda: self._set_theme("Light"))
        view_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Window
        self.window_menu: tk.Menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Window", menu=self.window_menu)
        self._rebuild_window_menu()

        # Language
        lang_menu = tk.Menu(self.menubar, tearoff=0)
        for lang in SYNTAX:
            lang_menu.add_command(label=lang, command=lambda l=lang: self._set_language(l))
        self.menubar.add_cascade(label="Language", menu=lang_menu)

        # Help
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="Welcome", command=self._open_welcome)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)

    # ── notebook (tabs area) ────────────────────────────────────────────
    def _build_notebook(self) -> None:
        style = ttk.Style()
        style.theme_use("default")
        self.main_pane: tk.PanedWindow = tk.PanedWindow(
            self.root,
            orient="horizontal",
            sashwidth=5,
            showhandle=False,
            bd=0,
            relief="flat",
        )
        self.main_pane.pack(fill="both", expand=True)
        self.notebook: ttk.Notebook = ttk.Notebook(self.main_pane)
        self.main_pane.add(self.notebook, minsize=360)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<Button-3>", self._show_tab_menu)
        self.notebook.bind("<Double-Button-1>", self._toggle_file_at_tab_area)

    def _build_markdown_viewer(self) -> None:
        frame = tk.Frame(self.main_pane, bg=self.theme["bg"], width=420)
        header = tk.Frame(frame, bg=self.theme["menu_bg"])
        header.pack(fill="x")
        title = tk.Label(
            header,
            text="Markdown View",
            anchor="w",
            padx=10,
            pady=6,
            bg=self.theme["menu_bg"],
            fg=self.theme["menu_fg"],
        )
        title.pack(side="left", fill="x", expand=True)
        tk.Button(header, text="X", width=3, command=self._close_markdown_view).pack(side="right", padx=4, pady=3)

        body = tk.Frame(frame, bg=self.theme["bg"])
        body.pack(fill="both", expand=True)
        vscroll = tk.Scrollbar(body, orient="vertical")
        vscroll.pack(side="right", fill="y")
        viewer = tk.Text(
            body,
            wrap="word",
            padx=16,
            pady=14,
            borderwidth=0,
            highlightthickness=0,
            state="disabled",
            cursor="arrow",
            yscrollcommand=vscroll.set,
            bg=self.theme["bg"],
            fg=self.theme["fg"],
        )
        viewer.pack(side="left", fill="both", expand=True)
        vscroll.config(command=viewer.yview)

        self.markdown_view_frame = frame
        self.markdown_view_text = viewer
        self.markdown_view_title = title

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
            size_text = self._format_file_size(tab.last_known_size)
            reload_text = "    |    Reload available" if tab.needs_reload else ""
            self.status_left.config(
                text=f"  Ln {line}, Col {int(col)+1}    |    Lines: {total}    |    {tab.language}    |    Size: {size_text}{reload_text}"
            )
            self.status_right.config(text=f"{tab.encoding}    Tab: {self.tab_size}    Zoom: {self.font_size}pt  ")
        except Exception:
            pass

    # ── keybindings ─────────────────────────────────────────────────────
    def _bind_shortcuts(self) -> None:
        r = self.root
        r.bind("<Control-n>", lambda e: self._new_file())
        r.bind("<Control-N>", lambda e: self._new_file())
        r.bind("<Control-o>", lambda e: self._open_file())
        r.bind("<Control-O>", lambda e: self._open_file())
        r.bind("<Control-s>", self._on_save_shortcut)
        r.bind("<Control-Shift-S>", self._on_save_as_shortcut)
        r.bind("<Control-p>", lambda e: self._print_preview())
        r.bind("<Control-P>", lambda e: self._print_preview())
        r.bind("<Control-w>", lambda e: self._close_tab())
        r.bind("<Control-W>", lambda e: self._close_tab())
        r.bind("<Control-f>", lambda e: self._open_find())
        r.bind("<Control-F>", lambda e: self._open_find())
        r.bind("<Control-h>", lambda e: self._open_replace())
        r.bind("<Control-H>", lambda e: self._open_replace())
        r.bind("<Control-comma>", lambda e: self._open_preferences())
        r.bind("<Control-g>", lambda e: self._go_to_line())
        r.bind("<Control-G>", lambda e: self._go_to_line())
        r.bind("<Control-d>", self._on_duplicate_line_shortcut)
        r.bind("<Control-D>", self._on_duplicate_line_shortcut)
        r.bind("<Control-slash>", self._on_toggle_comment_shortcut)
        r.bind("<Control-semicolon>", self._on_insert_datetime_shortcut)
        r.bind("<Control-Tab>", lambda e: self._next_tab())
        r.bind("<Control-Shift-Tab>", lambda e: self._previous_tab())
        r.bind("<Control-plus>", lambda e: self._zoom_in())
        r.bind("<Control-equal>", lambda e: self._zoom_in())
        r.bind("<Control-minus>", lambda e: self._zoom_out())
        r.bind("<Control-0>", lambda e: self._zoom_reset())
        r.bind("<Control-m>", lambda e: self._open_markdown_view())
        r.bind("<Control-M>", lambda e: self._open_markdown_view())

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
        skipped: List[str] = []
        for idx in range(count):
            length = shell32.DragQueryFileW(hdrop, idx, None, 0)
            buffer = ctypes.create_unicode_buffer(length + 1)
            shell32.DragQueryFileW(hdrop, idx, buffer, length + 1)
            path = buffer.value
            if not os.path.isfile(path):
                continue
            if self._is_text_file(path):
                self._open_dropped_file(path)
            else:
                skipped.append(path)
        shell32.DragFinish(hdrop)
        if skipped:
            names = "\n".join(os.path.basename(path) for path in skipped[:8])
            if len(skipped) > 8:
                names += f"\n... and {len(skipped) - 8} more"
            messagebox.showwarning(
                "Drag & Drop",
                "Only text-format files can be opened by drag and drop:\n\n" + names,
            )

    def _is_text_file(self, path: str) -> bool:
        """Return True when a sample of *path* looks like readable text."""
        try:
            with open(path, "rb") as f:
                sample = f.read(8192)
        except Exception:
            return False
        if not sample:
            return True
        if b"\x00" in sample:
            return self._looks_like_utf16_text(sample)
        control_chars = sum(
            1 for b in sample
            if b < 32 and b not in (9, 10, 12, 13)
        )
        return control_chars / len(sample) < 0.30

    def _looks_like_utf16_text(self, sample: bytes) -> bool:
        if sample.startswith((b"\xff\xfe", b"\xfe\xff")):
            return True
        if len(sample) < 4:
            return False

        even_nulls = sample[0::2].count(0)
        odd_nulls = sample[1::2].count(0)
        half_len = max(1, len(sample) // 2)
        likely_utf16le = odd_nulls / half_len > 0.25
        likely_utf16be = even_nulls / half_len > 0.25
        if not (likely_utf16le or likely_utf16be):
            return False

        encoding = "utf-16-le" if likely_utf16le else "utf-16-be"
        try:
            sample.decode(encoding)
            return True
        except UnicodeDecodeError:
            return False

    def _read_text_file(self, path: str) -> str:
        """Read a text file using common encodings before latin-1 fallback."""
        if not self._is_text_file(path):
            raise ValueError("This file appears to be binary, so it was not opened as text.")
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp949", "latin-1"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(path, "r", encoding="latin-1") as f:
            return f.read()

    def _normalize_startup_paths(self, paths: List[str]) -> List[str]:
        """Normalize file paths passed by command line or Windows file association."""
        normalized: List[str] = []
        seen = set()
        for raw_path in paths:
            if not raw_path:
                continue
            path = os.path.abspath(os.path.expanduser(raw_path.strip('"')))
            key = self._normalize_path(path)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(path)
        return normalized

    def _open_startup_files(self, paths: List[str]) -> bool:
        opened_any = False
        missing: List[str] = []
        for path in paths:
            if not os.path.isfile(path):
                missing.append(path)
                continue
            if self._open_path_in_tab(path, show_message=False):
                opened_any = True
        if missing:
            names = "\n".join(missing[:8])
            if len(missing) > 8:
                names += f"\n... and {len(missing) - 8} more"
            messagebox.showwarning("Open File", "These startup files were not found:\n\n" + names)
        return opened_any

    def _normalize_path(self, path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def _find_open_tab_by_path(self, path: str) -> Optional[EditorTab]:
        target = self._normalize_path(path)
        for tab in self.tabs:
            if tab.filepath and self._normalize_path(tab.filepath) == target:
                return tab
        return None

    def _find_open_tab_by_name(self, filename: str, exclude: Optional[EditorTab] = None) -> Optional[EditorTab]:
        target = filename.lower()
        for tab in self.tabs:
            if tab is exclude:
                continue
            if self._tab_title(tab).lower() == target:
                return tab
        return None

    def _focus_existing_open_file(self, tab: EditorTab, reason: str) -> None:
        self._select_tab(tab)
        messagebox.showinfo("Open File", f"{reason}\n\nSwitched to the existing tab.")

    def _can_open_file_path(self, path: str, show_message: bool = True) -> bool:
        same_path_tab = self._find_open_tab_by_path(path)
        if same_path_tab:
            if show_message:
                self._focus_existing_open_file(same_path_tab, "This file is already open.")
            else:
                self._select_tab(same_path_tab)
            return False

        same_name_tab = self._find_open_tab_by_name(os.path.basename(path))
        if same_name_tab:
            if show_message:
                self._focus_existing_open_file(
                    same_name_tab,
                    "A file with the same name is already open.",
                )
            else:
                self._select_tab(same_name_tab)
            return False
        return True

    def _new_title_number(self, title: Any) -> Optional[int]:
        if not isinstance(title, str):
            return None
        match = re.fullmatch(r"new(\d+)", title.strip(), flags=re.IGNORECASE)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _sync_new_file_counter(self, title: Any) -> None:
        number = self._new_title_number(title)
        if number is not None:
            self._new_file_counter = max(self._new_file_counter, number + 1)

    def _session_new_title(self, title: Any) -> str:
        title = title.strip() if isinstance(title, str) else ""
        legacy_prefix = "Un" + "titled"
        if re.fullmatch(rf"{legacy_prefix}(?:\s+\d+)?", title, flags=re.IGNORECASE):
            return self._next_new_title()
        if self._new_title_number(title) is not None:
            self._sync_new_file_counter(title)
            return title
        return title or self._next_new_title()

    def _next_new_title(self) -> str:
        existing = {self._tab_title(tab).lower() for tab in self.tabs}
        number = 1
        while True:
            title = f"new{number}"
            if title.lower() not in existing:
                self._new_file_counter = number + 1
                return title
            number += 1

    def _check_external_file_changes(self) -> None:
        """Mark open tabs when their backing files change outside the app."""
        try:
            for tab in list(self.tabs):
                if not tab.filepath or not os.path.exists(tab.filepath):
                    continue
                size = self._get_file_size(tab.filepath)
                mtime = self._get_file_mtime(tab.filepath)
                if tab.last_known_size is None and tab.last_known_mtime is None:
                    tab.last_known_size = size
                    tab.last_known_mtime = mtime
                    continue
                if size != tab.last_known_size or mtime != tab.last_known_mtime:
                    if not tab.needs_reload:
                        tab.needs_reload = True
                        self._update_tab_title(tab)
                        self._update_status()
                        self._rebuild_window_menu()
        finally:
            self.root.after(2000, self._check_external_file_changes)

    def _reload_current_file(self) -> None:
        tab = self.current_tab
        if tab:
            self._reload_tab(tab)

    def _reload_tab(self, tab: EditorTab) -> None:
        if not tab.filepath:
            return
        if tab.text.edit_modified():
            ans = messagebox.askyesnocancel(
                "Reload File",
                "This tab has unsaved edits. Reload from disk and discard those edits?",
            )
            if ans is not True:
                return
        try:
            content = self._read_text_file(tab.filepath)
        except Exception as exc:
            messagebox.showerror("Reload File", f"Unable to reload file:\n{tab.filepath}\n\n{exc}")
            return
        tab.text.delete("1.0", "end")
        tab.text.insert("1.0", content)
        tab.text.edit_modified(False)
        tab.modified = False
        tab.needs_reload = False
        tab.last_known_size = self._get_file_size(tab.filepath)
        tab.last_known_mtime = self._get_file_mtime(tab.filepath)
        tab.language = EXT_MAP.get(os.path.splitext(tab.filepath)[1].lower(), tab.language)
        self._select_tab(tab)
        self._update_tab_title(tab)
        self._highlight_syntax()
        self._redraw_line_numbers()
        self._update_status()
        self._rebuild_window_menu()
        self._record_file_history(tab.filepath)
        self._save_history()
        self._save_session()

    def _open_dropped_file(self, path: str) -> None:
        self._open_path_in_tab(path)

    # ── tab helpers ─────────────────────────────────────────────────────
    def _make_editor(self, parent: tk.Frame) -> Tuple[tk.Text, LineNumbers, Optional[tk.Scrollbar], tk.Frame, tk.Canvas, tk.Frame]:
        """Create a text widget + line-number canvas inside *parent* frame."""
        t = self.theme
        parent.configure(bg=t["bg"])
        frame = tk.Frame(parent, bg=t["bg"])
        frame.pack(fill="both", expand=True)

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
            inactiveselectbackground=t["select_bg"],
            borderwidth=0, highlightthickness=0, padx=12, pady=4,
            tabs=(self._tab_width_pixels(),),
        )
        margin_guide = tk.Frame(text, width=1, bg=self._a4_margin_guide_color())
        margin_guide.place_forget()

        # Scrollbars
        vscroll = tk.Scrollbar(frame, orient="vertical", command=text.yview)
        vscroll.pack(side="right", fill="y")
        minimap = tk.Canvas(frame, width=88, highlightthickness=0, bd=0, bg=self._minimap_bg_color())
        minimap_separator = tk.Frame(frame, width=1, bg=self._minimap_separator_color())
        text.pack(side="left", fill="both", expand=True)
        def _sync_yview(first: str, last: str) -> None:
            vscroll.set(first, last)
            self._redraw_line_numbers()
            if self.current_tab:
                self._draw_minimap(self.current_tab)
        text.config(yscrollcommand=_sync_yview)

        hscroll: Optional[tk.Scrollbar] = None
        if not self.word_wrap:
            hscroll = tk.Scrollbar(parent, orient="horizontal", command=text.xview)
            hscroll.pack(side="bottom", fill="x")
            text.config(xscrollcommand=hscroll.set)

        line_nums.text_widget = text

        # Events
        text.bind("<KeyRelease>", self._on_key_release)
        text.bind("<KeyPress>", self._on_key_press)
        text.bind("<Tab>", self._on_tab_key)
        text.bind("<Return>", self._on_return_key)
        text.bind("<Right>", self._on_commit_virtual_closer_key)
        text.bind("<Down>", self._on_commit_virtual_closer_key)
        text.bind("<ButtonRelease-1>", self._on_text_click_release)
        text.bind("<Double-ButtonRelease-1>", self._on_text_double_click_release)
        text.bind("<MouseWheel>", self._on_scroll)
        text.bind(
            "<Configure>",
            lambda e: (
                self._redraw_line_numbers(),
                self._update_a4_margin_guides(),
                self._draw_minimap(self.current_tab),
            ),
        )
        text.bind("<Button-3>", self._context_menu)
        text.bind("<Control-d>", self._on_duplicate_line_shortcut)
        text.bind("<Control-D>", self._on_duplicate_line_shortcut)
        text.bind("<Control-semicolon>", self._on_insert_datetime_shortcut)
        minimap.bind("<Configure>", lambda e: self._draw_minimap(self.current_tab))

        return text, line_nums, hscroll, margin_guide, minimap, minimap_separator

    def _clean_tab_title(self, title: str) -> str:
        title = title.strip()
        if title.startswith("*"):
            title = title[1:].strip()
        if title.endswith("[Reload]"):
            title = title[:-8].strip()
        return title or "new1"

    def _update_tab_title(self, tab: EditorTab) -> None:
        if tab not in self.tabs:
            return
        idx = self.notebook.index(tab.frame)
        title = os.path.basename(tab.filepath) if tab.filepath else self._tab_title(tab)
        if tab.modified or tab.text.edit_modified():
            title = f"*{title}"
        if tab.needs_reload:
            title = f"{title} [Reload]"
        self.notebook.tab(idx, text=f"  {title}  ")

    def _new_tab(
        self,
        title: str = "new1",
        content: str = "",
        filepath: Optional[str] = None,
        language: str = "Plain Text",
        last_known_size: Optional[int] = None,
        last_known_mtime: Optional[float] = None,
        mark_modified: bool = False,
    ) -> None:
        outer = tk.Frame(self.notebook, bg=self.theme["bg"])
        text, line_nums, hscroll, margin_guide, minimap, minimap_separator = self._make_editor(outer)
        if content:
            text.insert("1.0", content)
        if filepath and last_known_size is None:
            last_known_size = self._get_file_size(filepath)
        if filepath and last_known_mtime is None:
            last_known_mtime = self._get_file_mtime(filepath)
        tab = EditorTab(outer, text, line_nums, hscroll, margin_guide, filepath, language, last_known_size, last_known_mtime, title)
        tab.minimap = minimap
        tab.minimap_separator = minimap_separator
        minimap.bind("<Button-1>", lambda event, t=tab: self._on_minimap_click(t, event))
        self.tabs.append(tab)
        self.notebook.add(outer, text=f"  {title}  ")
        if filepath:
            tab.title = os.path.basename(filepath)
        else:
            self._sync_new_file_counter(title)
        tab.modified = mark_modified
        text.edit_modified(mark_modified)
        self._update_tab_title(tab)
        self.notebook.select(outer)
        self.current_tab = tab
        self._highlight_syntax()
        self._redraw_line_numbers()
        if self.current_tab:
            self._update_virtual_closer(self.current_tab)
            self._update_occurrence_preview(self.current_tab, self.current_tab.occurrence_query)
        self._update_a4_margin_guides()
        self._update_occurrence_preview(tab, "")
        self._update_status()
        self._rebuild_window_menu()

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
            self._update_virtual_closer(tab)
            self._update_occurrence_preview(tab, tab.occurrence_query)
            self._update_status()
            self._rebuild_window_menu()
            self._sync_markdown_view()

    # ── file operations ─────────────────────────────────────────────────
    def _new_file(self) -> None:
        self._new_tab(title=self._next_new_title())

    def _toggle_file_at_tab_area(self, event: tk.Event) -> str:
        tab = self._tab_at_event(event)
        if tab:
            self._close_tab(tab)
        else:
            self._new_file()
        return "break"

    def _on_save_shortcut(self, _event: tk.Event) -> str:
        self._save_file()
        return "break"

    def _on_save_as_shortcut(self, _event: tk.Event) -> str:
        self._save_file_as()
        return "break"

    def _on_insert_datetime_shortcut(self, _event: tk.Event) -> str:
        tab = self.current_tab
        if not tab:
            return "break"
        tab.text.insert(tk.INSERT, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self._after_programmatic_text_change(tab)
        return "break"

    def _on_tab_key(self, _event: tk.Event) -> str:
        tab = self.current_tab
        if not tab:
            return "break"
        tab.text.insert(tk.INSERT, " " * self.tab_size)
        self._after_programmatic_text_change(tab)
        return "break"

    def _on_return_key(self, _event: tk.Event) -> str:
        tab = self.current_tab
        if not tab:
            return "break"
        text = tab.text
        line_start = text.index("insert linestart")
        line_text = text.get(line_start, "insert lineend")
        indent = re.match(r"[ \t]*", line_text).group(0)
        text.insert(tk.INSERT, "\n" + indent)
        self._hide_virtual_closer(tab)
        self._after_programmatic_text_change(tab)
        return "break"

    def _after_programmatic_text_change(self, tab: EditorTab) -> None:
        tab.text.edit_modified(True)
        tab.modified = True
        self._update_tab_title(tab)
        self._schedule_highlight_syntax()
        self._redraw_line_numbers()
        self._draw_minimap(tab)
        self._update_status()
        self._sync_markdown_view()

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
        self._open_path_in_tab(path)

    def _open_path_in_tab(self, path: str, show_message: bool = True, add_to_recent: bool = True) -> bool:
        path = os.path.abspath(path)
        if not self._can_open_file_path(path, show_message=show_message):
            return self._find_open_tab_by_path(path) is not None
        try:
            content = self._read_text_file(path)
        except Exception as exc:
            if show_message:
                messagebox.showerror("Open File", f"Unable to open file:\n{path}\n\n{exc}")
            return False
        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Plain Text")
        self._new_tab(title=os.path.basename(path), content=content, filepath=path, language=lang)
        if add_to_recent:
            self._add_recent(path)
        return True

    def _save_file(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        save_path = tab.filepath.strip() if isinstance(tab.filepath, str) else ""
        if save_path:
            self._write_file(tab, save_path)
        else:
            self._save_file_as()
        self._save_session()

    def _save_file_as(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        initialfile = self._suggest_save_filename(tab)
        path = filedialog.asksaveasfilename(initialfile=initialfile, defaultextension=".txt", filetypes=[
            ("Text", "*.txt"),
            ("Python", "*.py"), ("C++", "*.cpp"),
            ("JavaScript", "*.js"),
            ("HTML", "*.html"), ("CSS", "*.css"),
            ("JSON", "*.json"), ("SQL", "*.sql"),
            ("Markdown", "*.md"), ("YAML", "*.yaml"),
            ("TOML", "*.toml"), ("All Files", "*.*"),
        ])
        if not path:
            return
        same_path_tab = self._find_open_tab_by_path(path)
        if same_path_tab and same_path_tab is not tab:
            self._focus_existing_open_file(same_path_tab, "Another tab is already using this file.")
            return
        same_name_tab = self._find_open_tab_by_name(os.path.basename(path), exclude=tab)
        if same_name_tab:
            self._focus_existing_open_file(
                same_name_tab,
                "Another open tab already has the same file name.",
            )
            return
        self._write_file(tab, path)
        tab.filepath = path
        tab.title = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()
        tab.language = EXT_MAP.get(ext, "Plain Text")
        self._update_tab_title(tab)
        self._highlight_syntax()
        self._update_status()
        self._add_recent(path)
        self._sync_markdown_view()
        self._save_session()

    def _suggest_save_filename(self, tab: EditorTab) -> str:
        if tab.filepath:
            return os.path.basename(tab.filepath)

        content = tab.text.get("1.0", "end-1c")
        first_text = ""
        for line in content.splitlines():
            first_text = line.strip()
            if first_text:
                break

        if first_text:
            stem = self._safe_filename_stem(first_text[:25])
        else:
            stem = self._safe_filename_stem(tab.title or "new1")
        return f"{stem or 'new1'}.txt"

    def _safe_filename_stem(self, text_value: str) -> str:
        stem = re.sub(r'[\\/:*?"<>|]+', "_", text_value.strip())
        stem = re.sub(r"\s+", " ", stem).strip(" .")
        reserved = {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
        }
        if stem.upper() in reserved:
            stem = f"{stem}_"
        return stem

    def _write_file(self, tab: EditorTab, path: str) -> None:
        content = tab.text.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        tab.modified = False
        tab.text.edit_modified(False)
        tab.last_known_size = self._get_file_size(path)
        tab.last_known_mtime = self._get_file_mtime(path)
        tab.needs_reload = False
        self._update_tab_title(tab)
        self._record_file_history(path)
        self._save_history()

    # ── print preview / print ───────────────────────────────────────────
    def _print_preview(self) -> None:
        tab = self.current_tab
        if not tab:
            return

        title = self._tab_title(tab)
        content = tab.text.get("1.0", "end-1c")
        orientation = tk.StringVar(value="portrait")
        page_index = tk.IntVar(value=0)

        win = tk.Toplevel(self.root)
        win.title("Print Preview - A4")
        win.geometry("900x700")
        win.minsize(720, 560)
        win.transient(self.root)

        toolbar = tk.Frame(win)
        toolbar.pack(fill="x", padx=10, pady=8)

        tk.Label(toolbar, text="Paper: A4").pack(side="left", padx=(0, 14))
        tk.Radiobutton(toolbar, text="Portrait", variable=orientation, value="portrait").pack(side="left")
        tk.Radiobutton(toolbar, text="Landscape", variable=orientation, value="landscape").pack(side="left", padx=(0, 14))

        page_label = tk.Label(toolbar, width=14, anchor="center")
        page_label.pack(side="left", padx=4)

        canvas = tk.Canvas(win, bg="#7A7A7A", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        pages: List[List[Tuple[Optional[int], str]]] = []

        def rebuild_pages() -> None:
            nonlocal pages
            pages = self._paginate_for_a4(content, orientation.get())
            page_index.set(min(page_index.get(), max(0, len(pages) - 1)))
            draw_page()

        def draw_page(event: Any = None) -> None:
            canvas.delete("all")
            if not pages:
                page_label.config(text="Page 0 / 0")
                return

            idx = page_index.get()
            page_label.config(text=f"Page {idx + 1} / {len(pages)}")

            paper_w_mm, paper_h_mm = self._a4_dimensions(orientation.get())
            margin = PRINT_MARGIN_MM
            available_w = max(1, canvas.winfo_width() - 40)
            available_h = max(1, canvas.winfo_height() - 40)
            scale = min(available_w / paper_w_mm, available_h / paper_h_mm)
            page_w = int(paper_w_mm * scale)
            page_h = int(paper_h_mm * scale)
            left = (canvas.winfo_width() - page_w) // 2
            top = (canvas.winfo_height() - page_h) // 2

            canvas.create_rectangle(left + 4, top + 4, left + page_w + 4, top + page_h + 4, fill="#555555", outline="")
            canvas.create_rectangle(left, top, left + page_w, top + page_h, fill="#FFFFFF", outline="#D0D0D0")

            text_left = left + int(margin * scale)
            text_top = top + int(margin * scale)
            preview_font_size = max(6, int(10 * scale / 2.8))
            preview_font = (self.font_family, preview_font_size)
            line_no_font = (self.font_family, max(5, preview_font_size - 1))
            line_height = max(9, int(preview_font_size * 1.55))
            line_no_width = max(18, int(preview_font_size * 3.8))
            code_left = text_left + line_no_width + max(4, int(3 * scale))

            canvas.create_text(
                text_left,
                text_top,
                anchor="nw",
                text=title,
                fill="#444444",
                font=(self.font_family, max(7, preview_font_size), "bold"),
            )
            y = text_top + line_height * 2
            for line_no, line in pages[idx]:
                if y > top + page_h - int(margin * scale):
                    break
                if line_no is not None:
                    canvas.create_text(
                        text_left + line_no_width,
                        y,
                        anchor="ne",
                        text=str(line_no),
                        fill="#A8A8A8",
                        font=line_no_font,
                    )
                canvas.create_text(
                    code_left,
                    y,
                    anchor="nw",
                    text=line,
                    fill="#111111",
                    font=preview_font,
                )
                y += line_height

        def prev_page() -> None:
            if page_index.get() > 0:
                page_index.set(page_index.get() - 1)
                draw_page()

        def next_page() -> None:
            if page_index.get() < len(pages) - 1:
                page_index.set(page_index.get() + 1)
                draw_page()

        tk.Button(toolbar, text="Previous", command=prev_page).pack(side="left", padx=2)
        tk.Button(toolbar, text="Next", command=next_page).pack(side="left", padx=2)
        tk.Button(toolbar, text="Print", command=lambda: self._print_current_tab(tab, orientation.get())).pack(side="right", padx=(8, 0))
        tk.Button(toolbar, text="Close", command=win.destroy).pack(side="right")

        orientation.trace_add("write", lambda *_: rebuild_pages())
        canvas.bind("<Configure>", draw_page)
        rebuild_pages()

    def _a4_dimensions(self, orientation: str) -> Tuple[int, int]:
        width, height = A4_SIZE_MM
        return (height, width) if orientation == "landscape" else (width, height)

    def _paginate_for_a4(self, content: str, orientation: str) -> List[List[Tuple[Optional[int], str]]]:
        paper_w_mm, paper_h_mm = self._a4_dimensions(orientation)
        body_w_mm = paper_w_mm - (PRINT_MARGIN_MM * 2)
        body_h_mm = paper_h_mm - (PRINT_MARGIN_MM * 2)
        px_per_mm = 96 / 25.4

        print_font = tkfont.Font(family=self.font_family, size=10)
        char_width = max(1, print_font.measure("M"))
        line_height = max(1, print_font.metrics("linespace"))
        line_no_width_px = print_font.measure("00000 ")
        chars_per_line = max(24, int(((body_w_mm * px_per_mm) - line_no_width_px) / char_width))
        lines_per_page = max(12, int((body_h_mm * px_per_mm) / line_height) - 2)

        wrapped_lines: List[Tuple[Optional[int], str]] = []
        for source_line_no, raw_line in enumerate(content.expandtabs(4).splitlines() or [""], start=1):
            if raw_line == "":
                wrapped_lines.append((source_line_no, ""))
                continue
            chunks = textwrap.wrap(
                raw_line,
                width=chars_per_line,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=True,
                break_on_hyphens=False,
            )
            if not chunks:
                wrapped_lines.append((source_line_no, ""))
                continue
            wrapped_lines.append((source_line_no, chunks[0]))
            wrapped_lines.extend((None, chunk) for chunk in chunks[1:])

        pages = [
            wrapped_lines[i:i + lines_per_page]
            for i in range(0, len(wrapped_lines), lines_per_page)
        ]
        return pages or [[(1, "")]]

    def _print_current_tab(self, tab: EditorTab, orientation: str) -> None:
        content = tab.text.get("1.0", "end-1c")
        title = self._tab_title(tab)
        html_path = self._write_print_html(title, content, orientation)
        try:
            webbrowser.open(self._path_to_file_url(html_path))
        except Exception as exc:
            messagebox.showerror("Print", f"Unable to open the Windows print dialog:\n{exc}")

    def _write_print_html(self, title: str, content: str, orientation: str) -> str:
        safe_title = html_escape(title)
        page_orientation = "landscape" if orientation == "landscape" else "portrait"
        source_lines = content.expandtabs(4).splitlines() or [""]
        line_count = len(source_lines)
        line_no_digits = max(2, len(str(line_count)))

        def render_line(line_no: int, text: str) -> str:
            return (
                "<div class=\"print-line\">"
                f"<span class=\"line-no\">{line_no}</span>"
                f"<span class=\"code-line\">{html_escape(text)}</span>"
                "</div>"
            )

        lines_html = "\n".join(
            render_line(line_no, line)
            for line_no, line in enumerate(source_lines, start=1)
        )
        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>
@page {{
  size: A4 {page_orientation};
  margin: {PRINT_MARGIN_MM}mm;
}}
html, body {{
  margin: 0;
  padding: 0;
}}
body {{
  font-family: Consolas, 'Courier New', monospace;
  font-size: 10pt;
  line-height: 1.35;
  color: #000;
}}
h1 {{
  font-size: 11pt;
  margin: 0 0 8mm 0;
  font-weight: 700;
}}
.print-code {{
  display: block;
  max-width: 100%;
}}
.print-line {{
  display: grid;
  grid-template-columns: {line_no_digits + 1}ch minmax(0, 1fr);
  column-gap: 1.5ch;
  min-height: 1.35em;
  align-items: start;
}}
.line-no {{
  color: #B8B8B8;
  text-align: right;
  user-select: none;
  white-space: pre;
}}
.code-line {{
  min-width: 0;
  max-width: 100%;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-all;
  line-break: anywhere;
}}
</style>
<script>
window.addEventListener('load', function () {{
  setTimeout(function () {{ window.print(); }}, 300);
}});
</script>
</head>
<body>
<h1>{safe_title}</h1>
<div class="print-code">
{lines_html}
</div>
</body>
</html>
"""
        fd, path = tempfile.mkstemp(prefix="phil_notepad_print_", suffix=".html", text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    def _path_to_file_url(self, path: str) -> str:
        return "file:///" + os.path.abspath(path).replace("\\", "/")

    def _close_tab(self, tab: Optional[EditorTab] = None) -> bool:
        if not self.tabs:
            return False
        tab = tab or self.current_tab
        if not tab:
            return False
        if tab.text.edit_modified():
            self._select_tab(tab)
            ans = messagebox.askyesnocancel("Save?", "Do you want to save changes before closing?")
            if ans is None:
                return False
            if ans:
                self._save_file()
        idx = self.notebook.index(tab.frame)
        self.notebook.forget(idx)
        self.tabs.remove(tab)
        if self.tabs:
            next_idx = min(idx, len(self.tabs) - 1)
            self.notebook.select(self.tabs[next_idx].frame)
        else:
            self.current_tab = None
        self._save_session()
        self._rebuild_window_menu()
        return True

    def _close_all_tabs(self) -> None:
        for tab in list(self.tabs):
            if not self._close_tab(tab):
                break

    def _close_other_tabs(self) -> None:
        keep = self.current_tab
        if not keep:
            return
        for tab in list(self.tabs):
            if tab is keep:
                continue
            if not self._close_tab(tab):
                break
        self._select_tab(keep)

    def _select_tab(self, tab: EditorTab) -> None:
        if tab in self.tabs:
            self.notebook.select(tab.frame)
            self.current_tab = tab
            self._update_status()

    def _add_recent(self, path: str) -> None:
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:20]
        self._record_file_history(path)
        self._rebuild_recent_menu()
        self._save_history()
        self._save_session()

    def _open_recent(self, path: str) -> None:
        if not os.path.exists(path):
            messagebox.showerror("Error", f"File not found:\n{path}")
            return
        self._open_path_in_tab(path)

    # ── window/tab management ───────────────────────────────────────────
    def _tab_title(self, tab: EditorTab) -> str:
        try:
            if tab.filepath:
                return os.path.basename(tab.filepath)
            idx = self.notebook.index(tab.frame)
            tab.title = self._clean_tab_title(self.notebook.tab(idx, "text"))
            return tab.title
        except Exception:
            return os.path.basename(tab.filepath) if tab.filepath else tab.title

    def _tab_sort_key(self, tab: EditorTab) -> Tuple[str, str]:
        return ((tab.filepath or self._tab_title(tab)).lower(), self._tab_title(tab).lower())

    def _rebuild_window_menu(self) -> None:
        if not hasattr(self, "window_menu"):
            return
        menu = self.window_menu
        menu.delete(0, "end")
        has_tabs = bool(self.tabs)
        menu.add_command(label="Next Window        Ctrl+Tab", command=self._next_tab, state=("normal" if has_tabs else "disabled"))
        menu.add_command(label="Previous Window    Ctrl+Shift+Tab", command=self._previous_tab, state=("normal" if has_tabs else "disabled"))
        menu.add_separator()
        menu.add_command(label="Move Window Left", command=lambda: self._move_current_tab(-1), state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Move Window Right", command=lambda: self._move_current_tab(1), state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Sort Windows by Name", command=self._sort_tabs_by_name, state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_separator()
        menu.add_command(label="Reload Current Window", command=self._reload_current_file, state=("normal" if self.current_tab and self.current_tab.filepath else "disabled"))
        menu.add_separator()
        menu.add_command(label="Close Window       Ctrl+W", command=self._close_tab, state=("normal" if has_tabs else "disabled"))
        menu.add_command(label="Close Other Windows", command=self._close_other_tabs, state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Close All Windows", command=self._close_all_tabs, state=("normal" if has_tabs else "disabled"))
        if not self.tabs:
            return
        menu.add_separator()
        for i, tab in enumerate(self.tabs, start=1):
            marker = "✓ " if tab is self.current_tab else "  "
            reload_marker = " [Reload]" if tab.needs_reload else ""
            label = f"{marker}{i}. {self._tab_title(tab)}{reload_marker}"
            menu.add_command(label=label, command=lambda t=tab: self._select_tab(t))

    def _show_tab_menu(self, event: Any) -> None:
        tab = self._tab_at_event(event)
        if not tab:
            return
        self._select_tab(tab)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Select", command=lambda: self._select_tab(tab))
        menu.add_separator()
        menu.add_command(label="Move Left", command=lambda: self._move_tab(tab, -1), state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Move Right", command=lambda: self._move_tab(tab, 1), state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Sort by Name", command=self._sort_tabs_by_name, state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_separator()
        menu.add_command(label="Reload", command=lambda: self._reload_tab(tab), state=("normal" if tab.filepath else "disabled"))
        menu.add_separator()
        menu.add_command(label="Close", command=lambda: self._close_tab(tab))
        menu.add_command(label="Close Others", command=self._close_other_tabs, state=("normal" if len(self.tabs) > 1 else "disabled"))
        menu.add_command(label="Close All", command=self._close_all_tabs)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _tab_at_event(self, event: Any) -> Optional[EditorTab]:
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return None
        if 0 <= idx < len(self.tabs):
            return self.tabs[idx]
        return None

    def _close_tab_at_event(self, event: Any) -> str:
        tab = self._tab_at_event(event)
        if tab:
            self._close_tab(tab)
        return "break"

    def _move_current_tab(self, delta: int) -> None:
        if self.current_tab:
            self._move_tab(self.current_tab, delta)

    def _move_tab(self, tab: EditorTab, delta: int) -> None:
        if tab not in self.tabs or len(self.tabs) < 2:
            return
        old_idx = self.tabs.index(tab)
        new_idx = max(0, min(len(self.tabs) - 1, old_idx + delta))
        if old_idx == new_idx:
            return
        self.tabs.pop(old_idx)
        self.tabs.insert(new_idx, tab)
        self.notebook.insert(new_idx, tab.frame)
        self._select_tab(tab)
        self._rebuild_window_menu()

    def _sort_tabs_by_name(self) -> None:
        current = self.current_tab
        self.tabs.sort(key=self._tab_sort_key)
        for idx, tab in enumerate(self.tabs):
            self.notebook.insert(idx, tab.frame)
        if current:
            self._select_tab(current)
        self._rebuild_window_menu()

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
        self._after_programmatic_text_change(tab)

    def _on_duplicate_line_shortcut(self, _event: tk.Event) -> str:
        self._duplicate_line()
        return "break"

    def _line_comment_token(self, language: str) -> Optional[str]:
        if language in {"Python", "YAML", "TOML"}:
            return "#"
        if language in {"C++", "JavaScript", "SQL"}:
            return "//" if language != "SQL" else "--"
        if language in {"Plain Text", "Markdown"}:
            return "#"
        return None

    def _toggle_comment(self) -> None:
        tab = self.current_tab
        if not tab:
            return
        token = self._line_comment_token(tab.language)
        if not token:
            messagebox.showinfo("Toggle Comment", f"Line comment is not available for {tab.language}.")
            return

        text = tab.text
        try:
            start_line = int(text.index("sel.first").split(".")[0])
            end_index = text.index("sel.last")
            end_line, end_col = (int(part) for part in end_index.split("."))
            if end_col == 0 and end_line > start_line:
                end_line -= 1
        except tk.TclError:
            start_line = end_line = int(text.index(tk.INSERT).split(".")[0])

        lines = [text.get(f"{line}.0", f"{line}.0 lineend") for line in range(start_line, end_line + 1)]
        meaningful = [line for line in lines if line.strip()]
        uncomment = bool(meaningful) and all(re.match(rf"^\s*{re.escape(token)} ?", line) for line in meaningful)

        for offset, line_no in enumerate(range(start_line, end_line + 1)):
            line_text = lines[offset]
            if not line_text.strip():
                continue
            indent = re.match(r"\s*", line_text).group(0)
            if uncomment:
                start = len(indent)
                after_token = start + len(token)
                text.delete(f"{line_no}.{start}", f"{line_no}.{after_token}")
                if text.get(f"{line_no}.{start}", f"{line_no}.{start}+1c") == " ":
                    text.delete(f"{line_no}.{start}", f"{line_no}.{start}+1c")
            else:
                text.insert(f"{line_no}.{len(indent)}", token + " ")

        self._after_programmatic_text_change(tab)

    def _on_toggle_comment_shortcut(self, _event: tk.Event) -> str:
        self._toggle_comment()
        return "break"

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
        win.geometry("600x150" if replace else "600x104")
        win.resizable(False, False)
        win.transient(self.root)
        win.configure(bg=self.theme["menu_bg"])
        win.columnconfigure(1, weight=1)

        find_var = tk.StringVar()
        repl_var = tk.StringVar()
        case_var = tk.BooleanVar(value=False)
        count_var_label = tk.StringVar(value="No results")

        label_opts = {"bg": self.theme["menu_bg"], "fg": self.theme["menu_fg"]}
        entry_opts = {
            "bg": self.theme["bg"],
            "fg": self.theme["fg"],
            "insertbackground": self.theme["caret"],
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": "#3C3C3C" if self.theme_name == "Dark" else "#CCCCCC",
            "highlightcolor": "#007ACC",
        }

        tk.Label(win, text="Find", **label_opts).grid(row=0, column=0, padx=(10, 6), pady=(10, 4), sticky="w")
        find_entry = tk.Entry(win, textvariable=find_var, width=34, **entry_opts)
        find_entry.grid(row=0, column=1, padx=4, pady=(10, 4), sticky="ew")
        tk.Label(win, textvariable=count_var_label, width=10, anchor="w", **label_opts).grid(row=0, column=2, padx=4, pady=(10, 4))

        nav_frame = tk.Frame(win, bg=self.theme["menu_bg"])
        nav_frame.grid(row=0, column=3, padx=(2, 10), pady=(10, 4), sticky="e")

        if replace:
            tk.Label(win, text="Replace", **label_opts).grid(row=1, column=0, padx=(10, 6), pady=4, sticky="w")
            repl_entry = tk.Entry(win, textvariable=repl_var, width=34, **entry_opts)
            repl_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        options = tk.Frame(win, bg=self.theme["menu_bg"])
        options.grid(row=(2 if replace else 1), column=1, columnspan=3, padx=4, pady=(4, 8), sticky="w")

        def _all_matches(query: str) -> List[Tuple[str, str]]:
            matches: List[Tuple[str, str]] = []
            if not query:
                return matches
            nocase = not case_var.get()
            idx = "1.0"
            count_var = tk.IntVar()
            while True:
                idx = tab.text.search(query, idx, stopindex="end", nocase=nocase, count=count_var)
                if not idx:
                    break
                chars = count_var.get()
                if chars <= 0:
                    break
                end = f"{idx}+{chars}c"
                matches.append((idx, end))
                idx = end
            return matches

        def _refresh_find_highlight() -> List[Tuple[str, str]]:
            tab.text.tag_remove("found", "1.0", "end")
            query = find_var.get()
            matches = _all_matches(query)
            for idx, end in matches:
                tab.text.tag_add("found", idx, end)
            tab.text.tag_config("found", background="#FFD700", foreground="#000000")
            tab.text.tag_raise("found")
            count_var_label.set(f"{len(matches)} found" if matches else "No results")
            self._update_occurrence_preview(tab, query)
            return matches

        def _move_match(backward: bool = False) -> None:
            query = find_var.get()
            matches = _refresh_find_highlight()
            if not query or not matches:
                return
            insert = tab.text.index(tk.INSERT)
            chosen = matches[-1] if backward else matches[0]
            for idx, end in matches:
                if backward and tab.text.compare(idx, "<", insert):
                    chosen = (idx, end)
                elif not backward and tab.text.compare(idx, ">", insert):
                    chosen = (idx, end)
                    break
            tab.text.mark_set(tk.INSERT, chosen[0])
            tab.text.see(chosen[0])
            tab.text.tag_remove("sel", "1.0", "end")
            tab.text.tag_add("sel", chosen[0], chosen[1])
            self._update_status()

        def _replace_next() -> None:
            query = find_var.get()
            replacement = repl_var.get()
            if not query:
                return
            nocase = not case_var.get()
            idx = tab.text.search(query, "insert", stopindex="end", nocase=nocase)
            if not idx:
                idx = tab.text.search(query, "1.0", stopindex="end", nocase=nocase)
            if idx:
                count_var = tk.IntVar()
                tab.text.search(query, idx, stopindex="end", nocase=nocase, count=count_var)
                end = f"{idx}+{count_var.get()}c"
                tab.text.delete(idx, end)
                tab.text.insert(idx, replacement)
                tab.text.mark_set(tk.INSERT, f"{idx}+{len(replacement)}c")
                self._after_programmatic_text_change(tab)
                self._highlight_syntax()
                _refresh_find_highlight()

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
            self._after_programmatic_text_change(tab)
            self._highlight_syntax()
            _refresh_find_highlight()

        def _close_find() -> None:
            tab.text.tag_remove("found", "1.0", "end")
            win.destroy()

        tk.Button(nav_frame, text="^", width=3, command=lambda: _move_match(True)).pack(side="left", padx=1)
        tk.Button(nav_frame, text="v", width=3, command=lambda: _move_match(False)).pack(side="left", padx=1)
        tk.Button(nav_frame, text="X", width=3, command=_close_find).pack(side="left", padx=1)
        tk.Checkbutton(
            options,
            text="Match case",
            variable=case_var,
            command=_refresh_find_highlight,
            bg=self.theme["menu_bg"],
            fg=self.theme["menu_fg"],
            selectcolor=self.theme["bg"],
            activebackground=self.theme["menu_bg"],
            activeforeground=self.theme["menu_fg"],
        ).pack(side="left", padx=(0, 8))
        tk.Button(options, text="Find All", command=_refresh_find_highlight, width=10).pack(side="left", padx=2)
        if replace:
            tk.Button(options, text="Replace", command=_replace_next, width=10).pack(side="left", padx=2)
            tk.Button(options, text="Replace All", command=_replace_all, width=10).pack(side="left", padx=2)
        find_var.trace_add("write", lambda *_: _refresh_find_highlight())
        win.protocol("WM_DELETE_WINDOW", _close_find)
        win.bind("<Escape>", lambda _event: _close_find())
        find_entry.bind("<Return>", lambda _event: (_move_match(False), "break")[1])
        find_entry.bind("<Shift-Return>", lambda _event: (_move_match(True), "break")[1])
        initial_query = self._occurrence_query_from_cursor(tab)
        if initial_query:
            find_var.set(initial_query)
            find_entry.selection_range(0, "end")
        find_entry.focus_set()

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

    # ── preferences ────────────────────────────────────────────────────
    def _preferred_font_family(self) -> str:
        try:
            families = set(tkfont.families(self.root))
        except Exception:
            families = set()
        for family in DEFAULT_FONT_CANDIDATES:
            if family in families:
                return family
        return "Consolas"

    def _korean_safe_font_family(self, family: str) -> str:
        if family not in LATIN_ONLY_FONT_FALLBACKS:
            return family
        preferred = self._preferred_font_family()
        return preferred if preferred not in LATIN_ONLY_FONT_FALLBACKS else family

    def _normalize_tab_size(self, value: Any) -> int:
        try:
            return max(1, min(16, int(value)))
        except Exception:
            return DEFAULT_TAB_SIZE

    def _normalize_color(self, value: Any, fallback: str) -> str:
        if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()):
            return value.strip().upper()
        return fallback

    def _contrast_text_color(self, color_value: str) -> str:
        color_value = self._normalize_color(color_value, "#000000").lstrip("#")
        try:
            red = int(color_value[0:2], 16)
            green = int(color_value[2:4], 16)
            blue = int(color_value[4:6], 16)
        except Exception:
            return "#000000"
        luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
        return "#000000" if luminance >= 150 else "#FFFFFF"

    def _tab_width_pixels(self) -> int:
        try:
            font_obj = tkfont.Font(family=self.font_family, size=self.font_size)
            return max(1, font_obj.measure(" " * self.tab_size))
        except Exception:
            return 32

    def _apply_tab_size(self) -> None:
        tab_width = self._tab_width_pixels()
        for tab in self.tabs:
            tab.text.config(tabs=(tab_width,))
        self._save_session()

    def _open_preferences(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Preferences")
        win.geometry("700x820")
        win.minsize(660, 760)
        win.transient(self.root)
        win.grab_set()

        main = ttk.Frame(win, padding=14)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        font_frame = ttk.LabelFrame(main, text="Editor Font", padding=10)
        font_frame.grid(row=0, column=0, sticky="ew")
        font_frame.columnconfigure(1, weight=1)

        try:
            families = sorted(set(tkfont.families(self.root)), key=str.lower)
        except Exception:
            families = list(DEFAULT_FONT_CANDIDATES)
        for family in DEFAULT_FONT_CANDIDATES:
            if family not in families:
                families.insert(0, family)

        family_var = tk.StringVar(value=self.font_family)
        size_var = tk.IntVar(value=self.font_size)
        tab_size_var = tk.IntVar(value=self.tab_size)
        occurrence_color_var = tk.StringVar(value=self.occurrence_color)
        occurrence_current_color_var = tk.StringVar(value=self.occurrence_current_color)

        ttk.Label(font_frame, text="Font family").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        family_box = ttk.Combobox(font_frame, textvariable=family_var, values=families)
        family_box.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(font_frame, text="Font size").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        size_box = tk.Spinbox(font_frame, from_=6, to=40, textvariable=size_var, width=8)
        size_box.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(font_frame, text="Tab size").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        tab_size_box = tk.Spinbox(font_frame, from_=1, to=16, textvariable=tab_size_var, width=8)
        tab_size_box.grid(row=2, column=1, sticky="w", pady=4)

        preview = tk.Text(font_frame, height=4, wrap="word", padx=8, pady=6)
        preview.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        preview.insert(
            "1.0",
            "한글 미리보기: 바른 글꼴로 문장이 또렷하게 보입니다\n"
            "English preview: Clear letters, symbols, and numbers 1234567890\n"
            "Code preview: def hello(name): print(f\"안녕, {name}\")",
        )
        preview.configure(state="disabled")

        view_frame = ttk.LabelFrame(main, text="View Settings", padding=10)
        view_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        view_frame.columnconfigure(1, weight=1)

        theme_var = tk.StringVar(value=self.theme_name)
        wrap_var = tk.BooleanVar(value=self.word_wrap)
        guide_var = tk.BooleanVar(value=self.show_a4_margin_guide)

        ttk.Label(view_frame, text="Theme").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            view_frame,
            textvariable=theme_var,
            values=list(THEMES.keys()),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="w", pady=4)
        ttk.Checkbutton(view_frame, text="Word wrap", variable=wrap_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(view_frame, text="A4 margin guide", variable=guide_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=4)

        color_frame = ttk.LabelFrame(main, text="Selection Match Colors", padding=10)
        color_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        color_frame.columnconfigure(1, weight=1)

        def _set_swatch(swatch: tk.Label, color_value: str) -> None:
            normalized = self._normalize_color(color_value, DEFAULT_OCCURRENCE_COLOR)
            swatch.configure(bg=normalized, fg=self._contrast_text_color(normalized), text=normalized)

        def _choose_color(var: tk.StringVar, swatch: tk.Label, title: str) -> None:
            _rgb, chosen = colorchooser.askcolor(color=var.get(), title=title, parent=win)
            if not chosen:
                return
            normalized = self._normalize_color(chosen, var.get())
            var.set(normalized)
            _set_swatch(swatch, normalized)

        ttk.Label(color_frame, text="All matches").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        occurrence_swatch = tk.Label(color_frame, width=14, relief="solid", bd=1, fg="#000000")
        occurrence_swatch.grid(row=0, column=1, sticky="w", pady=4)
        ttk.Button(
            color_frame,
            text="Choose...",
            command=lambda: _choose_color(occurrence_color_var, occurrence_swatch, "All match highlight color"),
        ).grid(row=0, column=2, sticky="e", padx=(8, 0), pady=4)

        ttk.Label(color_frame, text="Current match").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        occurrence_current_swatch = tk.Label(color_frame, width=14, relief="solid", bd=1, fg="#000000")
        occurrence_current_swatch.grid(row=1, column=1, sticky="w", pady=4)
        ttk.Button(
            color_frame,
            text="Choose...",
            command=lambda: _choose_color(occurrence_current_color_var, occurrence_current_swatch, "Current match highlight color"),
        ).grid(row=1, column=2, sticky="e", padx=(8, 0), pady=4)
        _set_swatch(occurrence_swatch, occurrence_color_var.get())
        _set_swatch(occurrence_current_swatch, occurrence_current_color_var.get())

        info_frame = ttk.LabelFrame(main, text="Current Values", padding=10)
        info_frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        info_frame.columnconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)

        current_language = self.current_tab.language if self.current_tab else "None"
        current_encoding = self.current_tab.encoding if self.current_tab else "None"
        current_path = self.current_tab.filepath if self.current_tab and self.current_tab.filepath else (
            self._tab_title(self.current_tab) if self.current_tab else "None"
        )
        settings_rows = [
            ("Font", f"{self.font_family}, {self.font_size}pt"),
            ("Tab size", str(self.tab_size)),
            ("Theme", self.theme_name),
            ("Word wrap", "On" if self.word_wrap else "Off"),
            ("A4 margin guide", "On" if self.show_a4_margin_guide else "Off"),
            ("All match color", self.occurrence_color),
            ("Current match color", self.occurrence_current_color),
            ("Current language", current_language),
            ("Current encoding", current_encoding),
            ("Open tabs", str(len(self.tabs))),
            ("Recent files", str(len(self.recent_files))),
            ("Window geometry", self.root.geometry()),
            ("Session file", _SESSION_FILE),
            ("Current file", current_path),
        ]
        for row, (label, value) in enumerate(settings_rows):
            ttk.Label(info_frame, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=2)
            value_label = ttk.Label(info_frame, text=value, wraplength=520)
            value_label.grid(row=row, column=1, sticky="ew", pady=2)

        def _refresh_preview(*_: Any) -> None:
            try:
                preview.configure(state="normal", font=(family_var.get(), int(size_var.get())))
                preview.configure(tabs=(max(1, tkfont.Font(font=preview["font"]).measure(" " * self._normalize_tab_size(tab_size_var.get()))),))
                preview.configure(state="disabled")
            except Exception:
                preview.configure(state="disabled")

        family_var.trace_add("write", _refresh_preview)
        size_var.trace_add("write", _refresh_preview)
        tab_size_var.trace_add("write", _refresh_preview)
        _refresh_preview()

        def _apply() -> None:
            family = family_var.get().strip() or self._preferred_font_family()
            try:
                size = max(6, min(40, int(size_var.get())))
            except Exception:
                size = self.font_size
            tab_size = self._normalize_tab_size(tab_size_var.get())

            theme_name = theme_var.get() if theme_var.get() in THEMES else self.theme_name
            if theme_name != self.theme_name:
                self._set_theme(theme_name)

            self.font_family = family
            self.font_size = size
            self.base_font_size = size
            self._apply_font()
            self.tab_size = tab_size
            self._apply_tab_size()

            new_wrap = bool(wrap_var.get())
            if new_wrap != self.word_wrap:
                self.word_wrap = new_wrap
                for tab in self.tabs:
                    self._apply_word_wrap_to_tab(tab)

            self.show_a4_margin_guide = bool(guide_var.get())
            self.occurrence_color = self._normalize_color(occurrence_color_var.get(), DEFAULT_OCCURRENCE_COLOR)
            self.occurrence_current_color = self._normalize_color(
                occurrence_current_color_var.get(),
                DEFAULT_OCCURRENCE_CURRENT_COLOR,
            )
            self._update_occurrence_preview(self.current_tab)
            self._update_a4_margin_guides()
            self._save_session()
            win.destroy()

        buttons = ttk.Frame(main)
        buttons.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(buttons, text="Apply", command=_apply).pack(side="right", padx=(0, 8))

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
        tab_width = self._tab_width_pixels()
        for tab in self.tabs:
            tab.text.config(font=fnt, tabs=(tab_width,))
        self._redraw_line_numbers()
        self._update_a4_margin_guides()
        self._update_occurrence_preview(self.current_tab)
        self._update_status()
        self._save_session()

    def _open_markdown_view(self) -> None:
        self._open_preview("markdown")

    def _open_preview(self, mode: str) -> None:
        tab = self.current_tab
        if not tab:
            return
        if not self._preview_allowed(mode, tab):
            self._close_markdown_view()
            messagebox.showinfo("Preview", self._preview_unavailable_message(mode))
            return
        if self.markdown_view_frame is None:
            self._build_markdown_viewer()
        if not self.markdown_view_visible and self.markdown_view_frame is not None:
            self.main_pane.add(self.markdown_view_frame, minsize=260, width=430)
            self.markdown_view_visible = True
        self.preview_mode = mode
        self._refresh_markdown_view()

    def _close_markdown_view(self) -> None:
        if self.markdown_view_frame is None:
            self.markdown_view_visible = False
            return
        try:
            self.main_pane.forget(self.markdown_view_frame)
        except Exception:
            pass
        self.markdown_view_visible = False

    def _is_markdown_tab(self, tab: Optional[EditorTab]) -> bool:
        if not tab or not tab.filepath:
            return False
        return os.path.splitext(tab.filepath)[1].lower() == ".md"

    def _tab_extension(self, tab: Optional[EditorTab]) -> str:
        if not tab or not tab.filepath:
            return ""
        return os.path.splitext(tab.filepath)[1].lower()

    def _preview_allowed(self, mode: str, tab: Optional[EditorTab]) -> bool:
        ext = self._tab_extension(tab)
        if mode == "markdown":
            return ext == ".md"
        if mode == "html":
            return ext in {".html", ".htm"}
        if mode == "table":
            return ext in {".csv", ".tsv"}
        if mode == "json":
            return ext == ".json"
        if mode == "diff":
            return bool(tab and tab.filepath and os.path.exists(tab.filepath))
        return tab is not None

    def _preview_unavailable_message(self, mode: str) -> str:
        if mode == "markdown":
            return "Markdown View is available only for .md files."
        if mode == "html":
            return "HTML Preview is available only for .html or .htm files."
        if mode == "table":
            return "CSV/TSV Preview is available only for .csv or .tsv files."
        if mode == "json":
            return "JSON Tree Preview is available only for .json files."
        if mode == "diff":
            return "Diff Preview needs a saved file on disk."
        return "Preview is not available for the current tab."

    def _preview_title(self, mode: str) -> str:
        return {
            "markdown": "Markdown View",
            "html": "HTML Preview",
            "table": "CSV/TSV Preview",
            "json": "JSON Tree Preview",
            "outline": "Outline Preview",
            "search": "Search Preview",
            "diff": "Diff Preview",
        }.get(mode, "Preview")

    def _sync_markdown_view(self) -> None:
        if not self.markdown_view_visible:
            return
        if not self._preview_allowed(self.preview_mode, self.current_tab):
            self._close_markdown_view()
            return
        self._refresh_markdown_view()

    def _refresh_markdown_view(self) -> None:
        tab = self.current_tab
        viewer = self.markdown_view_text
        if not self.markdown_view_visible or not self._preview_allowed(self.preview_mode, tab) or viewer is None:
            return
        if self.markdown_view_title is not None:
            self.markdown_view_title.config(text=f"{self._preview_title(self.preview_mode)} - {self._tab_title(tab)}")

        content = tab.text.get("1.0", "end-1c") if tab else ""
        viewer.configure(state="normal")
        viewer.delete("1.0", "end")
        self._configure_markdown_view_tags(viewer)
        if self.preview_mode == "markdown":
            self._render_markdown_preview(viewer, content)
        elif self.preview_mode == "html":
            self._render_html_preview(viewer, content)
        elif self.preview_mode == "table":
            self._render_table_preview(viewer, content, self._tab_extension(tab))
        elif self.preview_mode == "json":
            self._render_json_preview(viewer, content)
        elif self.preview_mode == "outline":
            self._render_outline_preview(viewer, content, tab.language if tab else "")
        elif self.preview_mode == "search":
            self._render_search_preview(viewer, content, tab)
        elif self.preview_mode == "diff":
            self._render_diff_preview(viewer, content, tab)
        viewer.configure(state="disabled")

    def _configure_markdown_view_tags(self, viewer: tk.Text) -> None:
        base_family = self.font_family
        viewer.configure(
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=(base_family, max(10, self.font_size)),
        )
        viewer.tag_configure("md_h1", font=(base_family, self.font_size + 8, "bold"), spacing1=12, spacing3=8)
        viewer.tag_configure("md_h2", font=(base_family, self.font_size + 5, "bold"), spacing1=10, spacing3=6)
        viewer.tag_configure("md_h3", font=(base_family, self.font_size + 3, "bold"), spacing1=8, spacing3=4)
        viewer.tag_configure("md_quote", lmargin1=18, lmargin2=18, foreground="#9CDCFE" if self.theme_name == "Dark" else "#57606A")
        viewer.tag_configure("md_list", lmargin1=20, lmargin2=38)
        viewer.tag_configure("md_code", font=("Cascadia Mono", max(9, self.font_size - 1)), background="#2A2A2A" if self.theme_name == "Dark" else "#F6F8FA")
        viewer.tag_configure("md_para", spacing1=2, spacing3=6)
        viewer.tag_configure("preview_muted", foreground="#9AA0A6" if self.theme_name == "Dark" else "#6A737D")
        viewer.tag_configure("preview_error", foreground="#F07178" if self.theme_name == "Dark" else "#B31D28")
        viewer.tag_configure("preview_added", foreground="#C3E88D" if self.theme_name == "Dark" else "#22863A")
        viewer.tag_configure("preview_removed", foreground="#F07178" if self.theme_name == "Dark" else "#B31D28")
        viewer.tag_configure("preview_info", foreground="#89DDFF" if self.theme_name == "Dark" else "#0969DA")

    def _render_markdown_preview(self, viewer: tk.Text, content: str) -> None:
        in_code = False
        for raw_line in content.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                viewer.insert("end", raw_line + "\n", ("md_code",))
                continue
            self._insert_markdown_view_line(viewer, line)

    def _render_html_preview(self, viewer: tk.Text, content: str) -> None:
        cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", content)
        cleaned = re.sub(r"(?i)<br\s*/?>", "\n", cleaned)
        cleaned = re.sub(r"(?i)</(p|div|section|article|header|footer|li|h[1-6]|tr)>", "\n", cleaned)
        cleaned = re.sub(r"(?is)<[^>]+>", "", cleaned)
        lines = [html_unescape(line).strip() for line in cleaned.splitlines()]
        text_lines = [line for line in lines if line]
        if not text_lines:
            viewer.insert("end", "No readable HTML text found.\n", ("preview_muted",))
            return
        for line in text_lines:
            viewer.insert("end", line + "\n", ("md_para",))

    def _render_table_preview(self, viewer: tk.Text, content: str, ext: str) -> None:
        delimiter = "\t" if ext == ".tsv" else ","
        try:
            rows = list(csv.reader(content.splitlines(), delimiter=delimiter))
        except Exception as exc:
            viewer.insert("end", f"Unable to parse table: {exc}\n", ("preview_error",))
            return
        if not rows:
            viewer.insert("end", "No rows found.\n", ("preview_muted",))
            return
        rows = rows[:250]
        widths = [0] * max(len(row) for row in rows)
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = min(40, max(widths[i], len(cell)))
        for r, row in enumerate(rows):
            cells = [
                (row[i] if i < len(row) else "")[:40].ljust(widths[i])
                for i in range(len(widths))
            ]
            tag = "md_code" if r == 0 else "md_para"
            viewer.insert("end", " | ".join(cells).rstrip() + "\n", (tag,))
        if len(rows) == 250:
            viewer.insert("end", "\nShowing first 250 rows.\n", ("preview_muted",))

    def _render_json_preview(self, viewer: tk.Text, content: str) -> None:
        try:
            value = json.loads(content)
        except Exception as exc:
            viewer.insert("end", f"Invalid JSON: {exc}\n", ("preview_error",))
            return
        self._insert_json_tree_node(viewer, value)

    def _insert_json_tree_node(self, viewer: tk.Text, value: Any, indent: int = 0, label: str = "") -> None:
        prefix = "  " * indent
        head = f"{prefix}{label}: " if label else prefix
        if isinstance(value, dict):
            viewer.insert("end", f"{head}{{{len(value)} keys}}\n", ("preview_info",))
            for key, child in value.items():
                self._insert_json_tree_node(viewer, child, indent + 1, str(key))
        elif isinstance(value, list):
            viewer.insert("end", f"{head}[{len(value)} items]\n", ("preview_info",))
            for i, child in enumerate(value[:200]):
                self._insert_json_tree_node(viewer, child, indent + 1, str(i))
            if len(value) > 200:
                viewer.insert("end", f"{prefix}  ... {len(value) - 200} more items\n", ("preview_muted",))
        else:
            viewer.insert("end", f"{head}{value!r}\n", ("md_para",))

    def _render_outline_preview(self, viewer: tk.Text, content: str, language: str) -> None:
        found = False
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            item = ""
            if language == "Markdown":
                match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
                if match:
                    item = f"{line_no}: {'  ' * (len(match.group(1)) - 1)}{match.group(2)}"
            elif language == "Python":
                match = re.match(r"^(class|def)\s+([A-Za-z_][\w]*)", stripped)
                if match:
                    item = f"{line_no}: {match.group(1)} {match.group(2)}"
            elif language == "HTML":
                match = re.match(r"<(h[1-6])[^>]*>(.*?)</\1>", stripped, flags=re.IGNORECASE)
                if match:
                    item = f"{line_no}: {html_unescape(re.sub(r'<[^>]+>', '', match.group(2))).strip()}"
            else:
                match = re.match(r"^\s*(def|class|function)\s+([A-Za-z_][\w]*)", line)
                if match:
                    item = f"{line_no}: {match.group(1)} {match.group(2)}"
            if item:
                found = True
                viewer.insert("end", item + "\n", ("md_para",))
        if not found:
            viewer.insert("end", "No outline items found.\n", ("preview_muted",))

    def _render_search_preview(self, viewer: tk.Text, content: str, tab: Optional[EditorTab]) -> None:
        query = (tab.occurrence_query if tab else "") or (self._occurrence_query_from_cursor(tab) if tab else "")
        query = query.strip()
        if not query:
            viewer.insert("end", "Double-click a word or select text first.\n", ("preview_muted",))
            return
        count = 0
        for line_no, line in enumerate(content.splitlines(), start=1):
            if query in line:
                count += 1
                viewer.insert("end", f"{line_no}: {line.strip()}\n", ("md_para",))
        if not count:
            viewer.insert("end", f"No matches for {query!r}.\n", ("preview_muted",))
        else:
            viewer.insert("1.0", f"{count} matches for {query!r}\n\n", ("preview_info",))

    def _render_diff_preview(self, viewer: tk.Text, content: str, tab: Optional[EditorTab]) -> None:
        if not tab or not tab.filepath:
            viewer.insert("end", "Diff needs a saved file.\n", ("preview_muted",))
            return
        try:
            disk_content = self._read_text_file(tab.filepath)
        except Exception as exc:
            viewer.insert("end", f"Unable to read saved file: {exc}\n", ("preview_error",))
            return
        diff = list(difflib.unified_diff(
            disk_content.splitlines(),
            content.splitlines(),
            fromfile="saved",
            tofile="current",
            lineterm="",
        ))
        if not diff:
            viewer.insert("end", "No differences from saved file.\n", ("preview_muted",))
            return
        for line in diff[:1000]:
            if line.startswith("+") and not line.startswith("+++"):
                tag = "preview_added"
            elif line.startswith("-") and not line.startswith("---"):
                tag = "preview_removed"
            elif line.startswith("@@"):
                tag = "preview_info"
            else:
                tag = "md_code"
            viewer.insert("end", line + "\n", (tag,))
        if len(diff) > 1000:
            viewer.insert("end", f"\nShowing first 1000 diff lines of {len(diff)}.\n", ("preview_muted",))

    def _insert_markdown_view_line(self, viewer: tk.Text, line: str) -> None:
        stripped = line.strip()
        if not stripped:
            viewer.insert("end", "\n")
            return
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(3, len(heading.group(1)))
            viewer.insert("end", heading.group(2) + "\n", (f"md_h{level}",))
            return
        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            viewer.insert("end", quote.group(1) + "\n", ("md_quote",))
            return
        bullet = re.match(r"^([-*+]|\d+\.)\s+(.*)$", stripped)
        if bullet:
            viewer.insert("end", f"  {bullet.group(1)} {bullet.group(2)}\n", ("md_list",))
            return
        viewer.insert("end", stripped + "\n", ("md_para",))

    # ── word wrap ───────────────────────────────────────────────────────
    def _toggle_word_wrap(self) -> None:
        self.word_wrap = not self.word_wrap
        for tab in self.tabs:
            self._apply_word_wrap_to_tab(tab)
        self._redraw_line_numbers()
        self._save_session()

    def _apply_word_wrap_to_tab(self, tab: EditorTab) -> None:
        if self.word_wrap:
            tab.text.config(wrap="word", xscrollcommand="")
            tab.text.xview_moveto(0)
            if tab.hscroll is not None:
                tab.hscroll.pack_forget()
            self._update_a4_margin_guide(tab)
            return

        tab.text.config(wrap="none")
        if tab.hscroll is None or not tab.hscroll.winfo_exists():
            tab.hscroll = tk.Scrollbar(tab.frame, orient="horizontal", command=tab.text.xview)
        tab.hscroll.pack(side="bottom", fill="x")
        tab.text.config(xscrollcommand=tab.hscroll.set)
        self._update_a4_margin_guide(tab)

    def _toggle_a4_margin_guide(self) -> None:
        self.show_a4_margin_guide = not self.show_a4_margin_guide
        self._update_a4_margin_guides()
        self._save_session()

    def _a4_margin_guide_color(self) -> str:
        return "#D18F00" if self.theme_name == "Light" else "#F6B93B"

    def _minimap_separator_color(self) -> str:
        return "#C8C8C8" if self.theme_name == "Light" else "#3E3E42"

    def _a4_margin_column(self) -> int:
        paper_w_mm, _ = self._a4_dimensions("portrait")
        body_w_mm = paper_w_mm - (PRINT_MARGIN_MM * 2)
        px_per_mm = 96 / 25.4
        guide_font = tkfont.Font(family=self.font_family, size=self.font_size)
        char_width = max(1, guide_font.measure("M"))
        return max(24, int((body_w_mm * px_per_mm) / char_width))

    def _update_a4_margin_guides(self) -> None:
        for tab in self.tabs:
            self._update_a4_margin_guide(tab)

    def _update_a4_margin_guide(self, tab: EditorTab) -> None:
        guide = tab.margin_guide
        if guide is None:
            return
        if not self.show_a4_margin_guide:
            guide.place_forget()
            return
        try:
            tab.text.update_idletasks()
            font_obj = tkfont.Font(font=tab.text["font"])
            char_width = max(1, font_obj.measure("M"))
            x = int(tab.text.cget("padx")) + (self._a4_margin_column() * char_width)
            visible_width = max(1, tab.text.winfo_width())
            if x < 0 or x > visible_width:
                guide.place_forget()
                return
            guide.configure(bg=self._a4_margin_guide_color())
            guide.place(x=x, y=0, width=1, relheight=1)
            guide.lift()
        except Exception:
            guide.place_forget()

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
        self._syntax_highlight_job = None
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

    def _schedule_highlight_syntax(self) -> None:
        if self._syntax_highlight_job is not None:
            try:
                self.root.after_cancel(self._syntax_highlight_job)
            except Exception:
                pass
        self._syntax_highlight_job = self.root.after_idle(self._highlight_syntax)

    # ── line numbers ────────────────────────────────────────────────────
    def _redraw_line_numbers(self) -> None:
        tab = self.current_tab
        if tab:
            tab.line_nums.redraw(self.theme)

    # ── occurrence preview / minimap ────────────────────────────────────
    def _minimap_bg_color(self) -> str:
        return "#252526" if self.theme_name == "Dark" else "#F3F3F3"

    def _minimap_line_color(self) -> str:
        return "#3C3C3C" if self.theme_name == "Dark" else "#D7D7D7"

    def _minimap_match_color(self) -> str:
        return "#D7BA7D" if self.theme_name == "Dark" else "#C19C00"

    def _minimap_cursor_color(self) -> str:
        return "#569CD6" if self.theme_name == "Dark" else "#007ACC"

    def _tab_needs_minimap(self, tab: EditorTab) -> bool:
        try:
            first, last = tab.text.yview()
            return first > 0.0 or last < 0.999
        except Exception:
            return False

    def _sync_minimap_visibility(self, tab: Optional[EditorTab] = None) -> bool:
        tab = tab or self.current_tab
        if not tab or not tab.minimap:
            return False
        show = self._tab_needs_minimap(tab)
        if show:
            if not tab.minimap.winfo_ismapped():
                tab.minimap.pack(side="right", fill="y", before=tab.text)
            if tab.minimap_separator and not tab.minimap_separator.winfo_ismapped():
                tab.minimap_separator.pack(side="right", fill="y", before=tab.text)
        else:
            tab.minimap.delete("all")
            tab.minimap.pack_forget()
            if tab.minimap_separator:
                tab.minimap_separator.pack_forget()
        return show

    def _occurrence_query_from_cursor(self, tab: EditorTab) -> str:
        text = tab.text
        try:
            if text.tag_ranges("sel"):
                selected = text.get("sel.first", "sel.last").strip()
                if selected:
                    return selected[:120]
        except tk.TclError:
            pass
        try:
            if text.compare(tk.INSERT, "==", "insert lineend"):
                return ""
            token = text.get("insert wordstart", "insert wordend").strip()
            if token:
                return token[:120]
            return ""
        except tk.TclError:
            return ""

    def _update_occurrence_preview(self, tab: Optional[EditorTab] = None, query: Optional[str] = None) -> None:
        tab = tab or self.current_tab
        if not tab:
            return
        text = tab.text
        text.tag_remove("occurrence", "1.0", "end")
        text.tag_remove("occurrence_current", "1.0", "end")
        query = self._occurrence_query_from_cursor(tab) if query is None else query.strip()
        tab.occurrence_query = query
        tab.occurrence_lines = []
        if query:
            nocase = False
            idx = "1.0"
            count_var = tk.IntVar()
            while True:
                idx = text.search(query, idx, stopindex="end", nocase=nocase, count=count_var)
                if not idx:
                    break
                chars = count_var.get()
                if chars <= 0:
                    break
                end = f"{idx}+{chars}c"
                text.tag_add("occurrence", idx, end)
                tab.occurrence_lines.append(int(idx.split(".")[0]))
                idx = end
            if tab.occurrence_lines:
                try:
                    current = text.index("insert")
                    current_end = f"{current}+{len(query)}c"
                    if text.get(current, current_end) == query:
                        text.tag_add("occurrence_current", current, current_end)
                except tk.TclError:
                    pass
        text.tag_config(
            "occurrence",
            background=self.occurrence_color,
            foreground=self._contrast_text_color(self.occurrence_color),
        )
        text.tag_config(
            "occurrence_current",
            background=self.occurrence_current_color,
            foreground=self._contrast_text_color(self.occurrence_current_color),
        )
        text.tag_raise("occurrence")
        text.tag_raise("occurrence_current")
        self._draw_minimap(tab)

    def _draw_minimap(self, tab: Optional[EditorTab] = None) -> None:
        tab = tab or self.current_tab
        if not tab or not tab.minimap:
            return
        canvas = tab.minimap
        if not self._sync_minimap_visibility(tab):
            return
        canvas.delete("all")
        canvas.configure(bg=self._minimap_bg_color())
        try:
            width = max(1, canvas.winfo_width())
            height = max(1, canvas.winfo_height())
            total = max(1, int(tab.text.index("end-1c").split(".")[0]))
            if height <= 1:
                return
            content_lines = tab.text.get("1.0", "end-1c").splitlines() or [""]
            sample_step = max(1, total // max(1, height // 2))
            for line_no in range(1, total + 1, sample_step):
                line = content_lines[line_no - 1] if line_no - 1 < len(content_lines) else ""
                if not line.strip():
                    continue
                y = int((line_no - 1) / max(1, total - 1) * (height - 1))
                line_width = max(1, min(max(1, width - 10), max(8, int(len(line.strip()) * 1.4))))
                canvas.create_line(6, y, 6 + line_width, y, fill=self._minimap_line_color())
            for line_no in tab.occurrence_lines:
                y = int((line_no - 1) / max(1, total - 1) * (height - 1))
                canvas.create_rectangle(1, max(0, y - 1), width - 2, min(height, y + 2), fill=self._minimap_match_color(), outline="")
            first, last = tab.text.yview()
            y1, y2 = int(first * height), int(last * height)
            canvas.create_rectangle(0, y1, width - 1, max(y1 + 8, y2), outline=self._minimap_cursor_color(), width=1)
        except Exception:
            pass

    def _on_minimap_click(self, tab: EditorTab, event: tk.Event) -> str:
        try:
            selection_ranges = tuple(tab.text.tag_ranges("sel"))
            selected_query = ""
            if len(selection_ranges) >= 2:
                selected_query = tab.text.get(selection_ranges[0], selection_ranges[1]).strip()
            total = max(1, int(tab.text.index("end-1c").split(".")[0]))
            height = max(1, tab.minimap.winfo_height() if tab.minimap else 1)
            line = max(1, min(total, int(event.y / height * total) + 1))
            self._select_tab(tab)
            tab.text.mark_set(tk.INSERT, f"{line}.0")
            tab.text.see(f"{line}.0")
            tab.text.tag_remove("sel", "1.0", "end")
            if len(selection_ranges) >= 2:
                tab.text.tag_add("sel", selection_ranges[0], selection_ranges[1])
                self._update_occurrence_preview(tab, selected_query)
            else:
                self._update_occurrence_preview(tab, tab.occurrence_query)
            self._update_status()
        except Exception:
            pass
        return "break"

    # ── event handlers ──────────────────────────────────────────────────
    def _on_key_press(self, event: Any = None) -> None:
        tab = self.current_tab
        if not tab or event is None:
            return
        pairs = {"'": "'", '"': '"', "{": "}", "[": "]", "(": ")"}
        char = getattr(event, "char", "")
        keysym = getattr(event, "keysym", "")
        if char in pairs:
            self._show_virtual_closer(tab, pairs[char])
        elif tab.virtual_close_char and char == tab.virtual_close_char:
            self._hide_virtual_closer(tab)
        elif keysym in {"Escape", "BackSpace", "Delete", "Left", "Up", "Home", "End"}:
            self._hide_virtual_closer(tab)

    def _on_commit_virtual_closer_key(self, _event: tk.Event) -> Optional[str]:
        tab = self.current_tab
        if not tab or not tab.virtual_close_char:
            return None
        tab.text.insert(tk.INSERT, tab.virtual_close_char)
        self._hide_virtual_closer(tab)
        self._after_programmatic_text_change(tab)
        return "break"

    def _on_key_release(self, event: Any = None) -> None:
        tab = self.current_tab
        if not tab:
            return
        # Modified indicator
        if tab.text.edit_modified():
            if not tab.modified:
                tab.modified = True
                self._update_tab_title(tab)
        self._schedule_highlight_syntax()
        self._update_virtual_closer(tab)
        self._redraw_line_numbers()
        self._draw_minimap(tab)
        self._update_status()
        self._sync_markdown_view()

    def _on_text_click_release(self, event: Any = None) -> None:
        self._on_key_release(event)

    def _on_text_double_click_release(self, event: Any = None) -> None:
        self._on_key_release(event)
        if self.current_tab:
            self._update_occurrence_preview(self.current_tab)

    def _on_scroll(self, event: Any = None) -> None:
        self.root.after(10, self._redraw_line_numbers)
        if self.current_tab:
            self.root.after(10, lambda: self._update_virtual_closer(self.current_tab))
            self.root.after(10, lambda: self._draw_minimap(self.current_tab))

    def _ghost_text_color(self) -> str:
        return "#B8B8B8" if self.theme_name == "Light" else "#6B6B6B"

    def _show_virtual_closer(self, tab: EditorTab, closer: str) -> None:
        tab.virtual_close_char = closer
        try:
            tab.virtual_close_line = tab.text.index(tk.INSERT).split(".")[0]
        except Exception:
            tab.virtual_close_line = ""
        self.root.after_idle(lambda: self._update_virtual_closer(tab))

    def _update_virtual_closer(self, tab: EditorTab) -> None:
        if not tab.virtual_close_char:
            self._hide_virtual_closer(tab)
            return
        try:
            line = tab.text.index(tk.INSERT).split(".")[0]
            if tab.virtual_close_line and line != tab.virtual_close_line:
                self._hide_virtual_closer(tab)
                return
            bbox = tab.text.bbox(tk.INSERT)
            if not bbox:
                self._hide_virtual_closer(tab, clear_state=False)
                return
            if tab.virtual_close_label is None or not tab.virtual_close_label.winfo_exists():
                tab.virtual_close_label = tk.Label(
                    tab.text,
                    font=tab.text["font"],
                    fg=self._ghost_text_color(),
                    bg=self.theme["bg"],
                    padx=0,
                    pady=0,
                    bd=0,
                )
            x, y, w, h = bbox
            label = tab.virtual_close_label
            label.configure(text=tab.virtual_close_char, fg=self._ghost_text_color(), bg=self.theme["bg"])
            label.place(x=x, y=y, width=max(w, tkfont.Font(font=tab.text["font"]).measure(tab.virtual_close_char)), height=h)
            label.lift()
        except Exception:
            self._hide_virtual_closer(tab)

    def _hide_virtual_closer(self, tab: EditorTab, clear_state: bool = True) -> None:
        if tab.virtual_close_label is not None:
            try:
                tab.virtual_close_label.place_forget()
            except Exception:
                pass
        if clear_state:
            tab.virtual_close_char = ""
            tab.virtual_close_line = ""

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
        menu.add_command(
            label="Reload",
            command=lambda: self._reload_tab(tab),
            state=("normal" if tab.filepath else "disabled"),
        )
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
        self._save_session()

    def _apply_theme(self) -> None:
        t = self.theme
        style = ttk.Style()
        try:
            desired_ttk_theme = "clam" if self.theme_name == "Dark" else "default"
            if style.theme_use() != desired_ttk_theme:
                style.theme_use(desired_ttk_theme)
        except tk.TclError:
            pass
        style.configure("TNotebook", background=t["tab_bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=t["tab_bg"], foreground=t["tab_fg"],
            padding=[12, 4],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", t["tab_sel_bg"]),
                ("active", t["tab_bg"]),
                ("pressed", t["tab_sel_bg"]),
                ("!selected", t["tab_bg"]),
            ],
            foreground=[
                ("selected", t["tab_sel_fg"]),
                ("active", t["tab_fg"]),
                ("!selected", t["tab_fg"]),
            ],
        )
        self.notebook.configure(style="TNotebook")
        self.status_frame.config(bg=t["status_bg"])
        self.status_left.config(bg=t["status_bg"], fg=t["status_fg"])
        self.status_right.config(bg=t["status_bg"], fg=t["status_fg"])
        self.root.config(bg=t["bg"])

        for tab in self.tabs:
            tab.frame.config(bg=t["bg"])
            for child in tab.frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=t["bg"])
            tab.text.config(
                bg=t["bg"], fg=t["fg"],
                insertbackground=t["caret"],
                selectbackground=t["select_bg"],
                selectforeground=t["select_fg"],
                inactiveselectbackground=t["select_bg"],
            )
            tab.line_nums.config(bg=t["line_bg"])
            if tab.minimap is not None:
                tab.minimap.configure(bg=self._minimap_bg_color())
                self._draw_minimap(tab)
            if tab.minimap_separator is not None:
                tab.minimap_separator.configure(bg=self._minimap_separator_color())
            if tab.margin_guide is not None:
                tab.margin_guide.configure(bg=self._a4_margin_guide_color())
        self._highlight_syntax()
        self._redraw_line_numbers()
        if self.current_tab:
            self._update_virtual_closer(self.current_tab)
        self._update_a4_margin_guides()
        if self.markdown_view_frame is not None:
            self.markdown_view_frame.config(bg=t["bg"])
            if self.markdown_view_text is not None:
                self._configure_markdown_view_tags(self.markdown_view_text)
            if self.markdown_view_title is not None:
                self.markdown_view_title.config(bg=t["menu_bg"], fg=t["menu_fg"])

    # ── next tab ────────────────────────────────────────────────────────
    def _next_tab(self) -> None:
        if len(self.tabs) < 2:
            return
        idx = self.notebook.index(self.notebook.select())
        nxt = (idx + 1) % len(self.tabs)
        self.notebook.select(self.tabs[nxt].frame)

    def _previous_tab(self) -> None:
        if len(self.tabs) < 2:
            return
        idx = self.notebook.index(self.notebook.select())
        prev = (idx - 1) % len(self.tabs)
        self.notebook.select(self.tabs[prev].frame)

    # ── help ────────────────────────────────────────────────────────────
    def _welcome_content(self) -> str:
        return (
            "╔══════════════════════════════════════════════╗\n"
            "║            Welcome to Notepad--             ║\n"
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
            "  Ctrl+/        Toggle comment\n"
            "  Ctrl+;        Insert date/time\n"
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
        )

    def _find_welcome_tab(self) -> Optional[EditorTab]:
        for tab in self.tabs:
            title = self._tab_title(tab).lower()
            if title in {"welcome", "welcome.txt"}:
                return tab
        return None

    def _load_builtin_welcome(self) -> None:
        tab = self._find_welcome_tab()
        if tab:
            self._select_tab(tab)
            tab.filepath = None
            tab.title = "Welcome"
            tab.last_known_size = None
            tab.last_known_mtime = None
            tab.text.delete("1.0", "end")
            tab.text.insert("1.0", self._welcome_content())
            tab.text.edit_modified(False)
            tab.modified = False
            tab.needs_reload = False
            tab.language = "Plain Text"
            self._update_tab_title(tab)
            self._highlight_syntax()
            self._update_occurrence_preview(tab, "")
            self._update_status()
            return
        self._new_tab(title="Welcome", content=self._welcome_content(), language="Plain Text")

    def _open_welcome(self) -> None:
        path = os.path.join(_BASE_DIR, "welcome.txt")
        if not os.path.exists(path):
            self._load_builtin_welcome()
            return
        existing = self._find_open_tab_by_path(path)
        if existing:
            self._reload_tab(existing)
            return
        if not self._can_open_file_path(path):
            return
        try:
            content = self._read_text_file(path)
        except Exception as exc:
            messagebox.showerror("Welcome", f"Unable to open welcome file:\n{path}\n\n{exc}")
            return
        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Plain Text")
        self._new_tab(title=os.path.basename(path), content=content, filepath=path, language=lang)

# ─── Entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = NotepadMinusMinus(root, startup_paths=sys.argv[1:])
    root.mainloop()
