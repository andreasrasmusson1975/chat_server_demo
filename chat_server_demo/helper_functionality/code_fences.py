
"""
code_fences.py
--------------
Utilities for detecting, validating, repairing, and normalizing code fences in markdown or text documents.

This module provides robust functions for working with code blocks delimited by triple backticks (```) or tildes (~~~).
It supports:
    - Heuristic language detection for code snippets
    - Validation of code fence correctness and structure
    - Automatic repair and normalization of code fences, including language tags and fence length
    - End-to-end workflows for ensuring all code blocks are properly fenced and formatted

Intended for use in LLM pipelines, markdown processors, and any application that needs to robustly handle code blocks in user-generated or programmatic text.
"""

import re
from typing import List, Tuple, Optional


OPEN_FENCE_RE = re.compile(r'^\s*([`~]{3,})\s*([A-Za-z0-9.+#_\-]*)\s*$')
CLOSE_FENCE_RE = re.compile(r'^\s*([`~]{3,})\s*$')
BACKTICKS_RUN_RE = lambda ch: re.compile(rf'{re.escape(ch)}+')

SECTION_MARKERS = ("### Improvements", "### Revised Answer", "### Comments")
ATX_HEADER_RE = re.compile(r'^[ \t]{0,3}#{3,6}[ \t]+')

def _prev_nonblank_is_blank(lines, idx: int) -> bool:
    # True if the immediately previous line exists and is blank
    return idx > 0 and lines[idx - 1].strip() == ""

def looks_like_section_boundary(lines, idx: int) -> bool:
    """
    Headers-only boundary detection:
      1) Explicit section markers always count.
      2) Otherwise, an ATX header (###..######) with a blank line before.
    """
    line = lines[idx].lstrip()

    # 1) Your explicit section headers (strongest signal)
    if any(line.startswith(m) for m in SECTION_MARKERS):
        return True

    # 2) Conservative ATX headings with a blank line before
    if ATX_HEADER_RE.match(lines[idx]) and _prev_nonblank_is_blank(lines, idx):
        return True

    return False

def guess_lang(code: str) -> Optional[str]:
    """
    Heuristically guess the programming or markup language of a code snippet.

    This function analyzes the provided code string and attempts to identify its language
    based on common syntax patterns, keywords, and structural cues. It supports detection
    for Python, JavaScript/TypeScript, Bash/Shell, SQL, HTML/XML, JSON, YAML, C/C++, Java, and Rust.

    Args:
        code (str): The code snippet to analyze.

    Returns:
        Optional[str]: The guessed language name (e.g., "python", "javascript", "bash", etc.),
        or None if the language cannot be determined.

    Detection Logic:
        - Uses regular expressions and keyword checks for language-specific features.
        - Returns the first matching language in priority order.
        - Returns None if no known language patterns are found.
    Example:
        >>> guess_lang("def my_function():\n    print('Hello, World!')")
    """
    s = code.strip()
    low = s.lower()

    # Python
    if re.search(r'^\s*def\s+\w+\s*\(', s, re.M) or "import " in low or "print(" in s:
        return "python"
    # JavaScript / TypeScript
    if "console.log(" in s or re.search(r'function\s+\w+\s*\(', s) or "=> " in s or re.search(r'\bimport\s+.*\s+from\s+', low):
        return "javascript"
    # Bash / Shell
    if re.search(r'^\s*\$?\s*(cd|ls|echo|export|pip|apt|yum|curl|wget|git)\b', low, re.M):
        return "bash"
    # SQL
    if re.search(r'\bselect\b.*\bfrom\b', low) or re.search(r'\bcreate\s+table\b', low):
        return "sql"
    # HTML / XML
    if low.startswith("<!doctype html") or re.search(r'^\s*<html\b', low, re.M) or low.startswith("<?xml"):
        return "html"
    # JSON
    if re.fullmatch(r'\s*\{[\s\S]*\}\s*', s) and ":" in s:
        return "json"
    # YAML
    if re.search(r'^\s*[\w\-]+\s*:\s*.+', s, re.M) and not (";" in s or "{" in s):
        return "yaml"
    # C/C++
    if "#include" in s or re.search(r'\bint\s+main\s*\(', s):
        return "c"
    # Java
    if re.search(r'\bpublic\s+class\b', s) or re.search(r'\bSystem\.out\.println\(', s):
        return "java"
    # Rust
    if "fn main()" in s or "let mut " in s:
        return "rust"
    return None

def validate_code_fences(text: str) -> Tuple[bool, List[str]]:
    """
    Validate the correctness of code fences in a markdown or text document.

    This function checks for common issues with code fences (triple backticks or tildes), such as:
      - Unclosed code blocks (opened but not closed)
      - Stray closing fences (closing without a corresponding opening)
      - Mismatched fence characters or lengths

    Args:
        text (str): The markdown or text content to validate.

    Returns:
        Tuple[bool, List[str]]: A tuple where the first element is True if all code fences are valid,
        and the second element is a list of human-readable issues found (empty if valid).

    Validation Logic:
        - Scans line by line for opening and closing code fences.
        - Tracks nesting and ensures all opened fences are properly closed.
        - Reports the line number of any unclosed or stray fences.
    """
    
    issues: List[str] = []
    lines = text.splitlines()
    in_block = False
    fence_char = None
    fence_len = 0
    open_line = 0
    # Detect unclosed fences
    for i, line in enumerate(lines, 1):
        if not in_block:
            m = OPEN_FENCE_RE.match(line)
            if m:
                in_block = True
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                open_line = i
        else:
            m2 = CLOSE_FENCE_RE.match(line)
            if m2 and m2.group(1)[0] == fence_char and len(m2.group(1)) >= fence_len:
                in_block = False
                fence_char = None
                fence_len = 0
    if in_block:
        issues.append(f"Unclosed code fence started on line {open_line}")

    # Detect stray closing fences
    depth = 0
    for i, line in enumerate(lines, 1):
        if OPEN_FENCE_RE.match(line):
            depth += 1
        elif CLOSE_FENCE_RE.match(line):
            if depth == 0:
                issues.append(f"Closing fence without opening on line {i}")
            else:
                depth -= 1

    return (len(issues) == 0), issues

def fix_code_fences(
    text: str,
    default_lang: Optional[str] = None,
    keep_fence_char: bool = True,
) -> Tuple[str, List[str]]:
    """
    Normalize and repair code fences in markdown or text content.

    This function scans the input text for code blocks delimited by triple backticks (```) or tildes (~~~),
    and ensures that all code fences are properly closed, have consistent length, and use normalized language tags.
    It can also add missing language tags (using heuristics or a default), and optionally standardize the fence character.

    Args:
        text (str): The markdown or text content to process.
        default_lang (Optional[str], optional): Language tag to use if none is detected or guessed. Defaults to None.
        keep_fence_char (bool, optional): If True, preserves the original fence character (` or ~); if False, uses backticks. Defaults to True.

    Returns:
        Tuple[str, List[str]]: A tuple containing the fixed text and a list of human-readable change descriptions.

    Normalization Logic:
        - Ensures every opened code fence is closed.
        - Adjusts fence length to avoid conflicts with code content.
        - Normalizes or adds language tags (using guess_lang or default_lang).
        - Optionally standardizes fence characters.
        - Logs all changes made for transparency.
    """
    lines = text.splitlines()
    out: List[str] = []
    changes: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        m = OPEN_FENCE_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        # Found an opening fence
        orig_series = m.group(1)
        fence_char = orig_series[0] if keep_fence_char else "`"
        fence_len = len(orig_series)
        lang = (m.group(2) or "").strip()
        code_buf: List[str] = []
        i += 1

        # Collect until matching close
        closed = False
        while i < len(lines):
            m2 = CLOSE_FENCE_RE.match(lines[i])
            if m2 and m2.group(1)[0] == orig_series[0] and len(m2.group(1)) >= fence_len:
                closed = True
                i += 1
                break
            if looks_like_section_boundary(lines, i):
                closed = True
                changes.append(f"Inserted missing closing fence before heading at line {i+1}")
                # do NOT consume this line; let the outer loop handle it as prose
                break
            code_buf.append(lines[i])
            i += 1
        code = "\n".join(code_buf)

        # Choose safe fence length (if code contains runs of the fence char)
        runs = [len(x.group(0)) for x in BACKTICKS_RUN_RE(fence_char).finditer(code)]
        safe_len = max(3, (max(runs) + 1) if runs else 3)

        # Normalize language tag
        norm_lang = lang.lower()
        if not norm_lang:
            g = guess_lang(code)
            if g:
                norm_lang = g
                changes.append("Added guessed language tag: " + g)
            elif default_lang:
                norm_lang = default_lang.lower()
                changes.append("Added default language tag: " + norm_lang)

        # Rebuild the fenced block
        opener = fence_char * safe_len + (f" {norm_lang}" if norm_lang else "")
        closer = fence_char * safe_len

        if fence_len != safe_len:
            changes.append(f"Adjusted fence length from {fence_len} to {safe_len}")
        if not closed:
            changes.append("Inserted missing closing fence at end of block")
        if lang != norm_lang and (lang or norm_lang):
            changes.append(f"Normalized language tag from '{lang}' to '{norm_lang or ''}'")

        out.append(opener)
        if code_buf:
            out.append(code)
        out.append(closer)

    fixed = "\n".join(out)
    return fixed, changes

# Convenience wrapper that validates, fixes, and validates again
def ensure_fenced_code(
    text: str,
    default_lang: Optional[str] = None,
    keep_fence_char: bool = True,
) -> Tuple[str, List[str]]:
    """
    Validate, repair, and normalize all code fences in a markdown or text document.

    This function acts as a convenience wrapper that first checks for code fence issues using
    `validate_code_fences`, attempts to fix any problems with `fix_code_fences`, and then re-validates.
    It also normalizes code fences even if the input is already valid, ensuring consistent formatting
    and language tagging throughout the document.

    Args:
        text (str): The markdown or text content to process.
        default_lang (Optional[str], optional): Language tag to use if none is detected or guessed. Defaults to None.
        keep_fence_char (bool, optional): If True, preserves the original fence character (` or ~); if False, uses backticks. Defaults to True.

    Returns:
        Tuple[str, List[str]]: A tuple containing the fixed text and a list of issues and/or changes made.

    Workflow:
        1. Validate code fences in the input text.
        2. If invalid, attempt to fix and re-validate, reporting all issues and changes.
        3. If valid, optionally normalize for consistency.
        4. Return the processed text and a log of all changes or issues found.
    """
    ok, issues = validate_code_fences(text)
    changes: List[str] = []
    if not ok:
        fixed, changes = fix_code_fences(text, default_lang=default_lang, keep_fence_char=keep_fence_char)
        ok2, issues2 = validate_code_fences(fixed)
        return fixed, (issues + changes + (["Still invalid after fix"] if not ok2 else []))
    # Even if valid, you can still normalize (optional)
    fixed, changes = fix_code_fences(text, default_lang=default_lang, keep_fence_char=keep_fence_char)
    return fixed, changes

