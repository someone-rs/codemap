# Python 3.9+

LANGUAGE_MAP = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".pl": "Perl",
    ".lua": "Lua",
    ".r": "R",
    ".jl": "Julia",
    ".dart": "Dart",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".less": "CSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "INI",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".rst": "Markdown",
    ".txt": "Text",
    ".xml": "XML",
    ".dockerfile": "Dockerfile",
    ".makefile": "Makefile",
    ".cmake": "CMake",
    ".gradle": "Gradle",
}

# Filenames without (or with special) extensions.
FILENAME_MAP = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
    "cmakelists.txt": "CMake",
    "rakefile": "Ruby",
    "gemfile": "Ruby",
    "vagrantfile": "Ruby",
    "podfile": "Ruby",
    "brewfile": "Ruby",
}

# Distinct, pleasant colors per language (used by treemap + charts).
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Scala": "#c22d40",
    "Perl": "#0298c3",
    "Lua": "#000080",
    "R": "#198CE7",
    "Julia": "#a270ba",
    "Dart": "#00B4AB",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "TOML": "#9c4221",
    "INI": "#777777",
    "SQL": "#e38c00",
    "Shell": "#89e051",
    "PowerShell": "#012456",
    "Markdown": "#083fa1",
    "Text": "#999999",
    "XML": "#0060ac",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "CMake": "#DA3434",
    "Gradle": "#02303A",
    "Other": "#cccccc",
}

DEFAULT_COLOR = "#cccccc"


def detect_language(filename):
    """Return the language name for a file, or 'Other' if unknown."""
    base = filename.rsplit("/", 1)[-1].lower()
    if base in FILENAME_MAP:
        return FILENAME_MAP[base]
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1]
        if ext in LANGUAGE_MAP:
            return LANGUAGE_MAP[ext]
    return "Other"


def color_for(language):
    return LANGUAGE_COLORS.get(language, DEFAULT_COLOR)
