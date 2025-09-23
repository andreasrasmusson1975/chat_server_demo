"""
Code fence processing and validation module for the MPAI Assistant chat server demo.

This module provides comprehensive utilities for parsing, validating, normalizing, and
repairing code fences in markdown and text content. It implements robust algorithms
for handling triple-backtick and triple-tilde code blocks commonly used in markdown
documents, chat applications, and documentation systems, ensuring proper formatting
and syntax highlighting support across the application.

Key Features:
    - Code fence validation with detailed error reporting
    - Automatic repair of malformed or incomplete code blocks
    - Language detection using heuristic analysis
    - Fence character normalization and length adjustment
    - Section boundary detection for intelligent code block closure
    - Support for both backtick (```) and tilde (~~~) fence styles
    - Robust handling of nested and overlapping fence scenarios
    - Comprehensive logging of all modifications and repairs

The module addresses common issues encountered when processing user-generated content
containing code blocks, such as unclosed fences, mismatched fence characters, missing
language tags, and conflicts between fence delimiters and code content. It provides
both validation-only and repair functionality to suit different application needs.

Architecture:
    The module implements a multi-layered approach with separate validation and repair
    phases. Validation functions identify issues without modification, while repair
    functions apply intelligent fixes based on context analysis and heuristic rules.
    Language detection uses pattern matching and keyword analysis to automatically
    identify programming languages.

Classes:
    None (module contains only functions and regex patterns)

Functions:
    Core Validation and Repair:
        validate_code_fences: Check code fence correctness and identify issues
        fix_code_fences: Repair malformed code fences with detailed change logging
        ensure_fenced_code: Complete validation and repair workflow

    Language Processing:
        guess_lang: Heuristic programming language detection

    Utility Functions:
        looks_like_section_boundary: Document structure analysis
        _prev_nonblank_is_blank: Line analysis helper

Constants:
    OPEN_FENCE_RE: Regex pattern for opening code fence detection
    CLOSE_FENCE_RE: Regex pattern for closing code fence detection
    BACKTICKS_RUN_RE: Dynamic regex factory for fence character runs
    SECTION_MARKERS: Predefined section header patterns
    ATX_HEADER_RE: Regex pattern for ATX-style markdown headers

Dependencies:
    - re: Regular expression operations for pattern matching
    - typing: Type hints for improved code clarity and IDE support

Author: Andreas Rasmusson
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
    Determine if a line represents a document section boundary or heading.

    This function analyzes a specific line within a document to determine whether
    it represents a structural boundary that should terminate an open code block.
    It implements intelligent heuristics to identify section headers, markdown
    headings, and other content divisions that indicate the logical end of a
    code block even when no explicit closing fence is present.

    The function supports two primary detection mechanisms: explicit section
    markers that are predefined in the application context, and standard
    markdown ATX headings with appropriate formatting context. This dual
    approach ensures robust boundary detection across various document styles
    and user-generated content patterns.

    Parameters
    ----------
    lines : list of str
        The complete list of lines from the document being analyzed. This
        provides the necessary context for examining the target line and
        its surrounding content for proper boundary detection.
    idx : int
        The zero-based index of the line to analyze within the lines list.
        Must be a valid index within the bounds of the lines list. The
        function will examine this line and potentially preceding lines
        for context-dependent boundary detection.

    Returns
    -------
    bool
        True if the line at the specified index represents a section boundary
        that should terminate an open code block, False otherwise. Returns
        True for explicit section markers and properly formatted ATX headings
        with appropriate preceding blank lines.
    """
    line = lines[idx].lstrip()

    # 1) Explicit section headers (strongest signal)
    if any(line.startswith(m) for m in SECTION_MARKERS):
        return True

    # 2) Conservative ATX headings with a blank line before
    if ATX_HEADER_RE.match(lines[idx]) and _prev_nonblank_is_blank(lines, idx):
        return True

    return False

def guess_lang(code: str) -> Optional[str]:
    """
    Heuristically identify the programming or markup language of a code snippet.

    This function analyzes code content using pattern matching and keyword detection
    to automatically determine the most likely programming language. It employs a
    priority-based detection system that examines syntax patterns, keywords, and
    structural characteristics specific to each supported language, enabling
    automatic language tagging for code fences in markdown content.

    The detection algorithm uses a combination of regular expressions and string
    matching to identify language-specific features such as function declarations,
    import statements, built-in functions, and distinctive syntax patterns. Languages
    are checked in a specific order to handle overlapping features and ensure the
    most accurate detection for common programming languages.

    Parameters
    ----------
    code : str
        The source code snippet to analyze for language detection. Can contain
        multiple lines and various code constructs. The function analyzes the
        entire content for language-specific patterns and keywords.

    Returns
    -------
    Optional[str]
        The detected language name as a lowercase string (e.g., "python", 
        "javascript", "bash", "sql", "html", "json", "yaml", "c", "java", "rust"),
        or None if no supported language patterns are found in the code.
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
    Validate the structural correctness of code fences in markdown content.

    This function performs comprehensive validation of code fence syntax in markdown
    or text documents, identifying common structural issues without modifying the
    content. It checks for proper opening and closing of code blocks, matching
    fence characters, and correct nesting patterns to ensure the document follows
    valid markdown code fence conventions.

    The validation process examines the entire document for fence-related issues
    including unclosed code blocks, orphaned closing fences, and mismatched fence
    character types or lengths. It provides detailed error reporting with line
    numbers to facilitate debugging and manual correction of problematic content.

    Parameters
    ----------
    text : str
        The markdown or text content to validate for code fence correctness.
        Can contain multiple code blocks, mixed fence types (backticks and tildes),
        and various content structures. The function analyzes the complete text
        for structural fence issues.

    Returns
    -------
    Tuple[bool, List[str]]
        A tuple containing two elements:
        - bool: True if all code fences are structurally valid, False if issues exist
        - List[str]: A list of human-readable issue descriptions with line numbers,
          empty if no issues are found. Each issue includes specific details about
          the problem location and nature for debugging purposes.
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
    Automatically repair and normalize malformed code fences in markdown content.

    This function provides comprehensive repair capabilities for broken, incomplete,
    or inconsistent code fence structures in markdown documents. It implements
    intelligent algorithms to detect and fix common issues including unclosed
    code blocks, missing language tags, fence length conflicts, and section
    boundary detection for automatic code block termination.

    The repair process maintains document integrity while applying standardization
    rules for consistent formatting across the entire document. It preserves code
    content while ensuring proper fence structure, enabling reliable syntax
    highlighting and markdown processing in downstream applications.

    Parameters
    ----------
    text : str
        The markdown or text content containing code fences to repair and normalize.
        Can include multiple code blocks with various issues such as missing
        closing fences, inconsistent fence lengths, or missing language tags.
        The function processes the entire document comprehensively.
    default_lang : Optional[str], default=None
        The default language tag to apply when no language can be detected
        automatically and no existing language tag is present. If None,
        code blocks without detectable languages will remain untagged.
        Common values include "python", "javascript", "bash", "sql", etc.
    keep_fence_char : bool, default=True
        Whether to preserve the original fence character type (backticks or tildes)
        found in each code block. If True, maintains the original character choice.
        If False, standardizes all fences to use backticks (```), providing
        consistency across the document.

    Returns
    -------
    Tuple[str, List[str]]
        A tuple containing two elements:
        - str: The repaired and normalized markdown content with all code fence
          issues resolved and standardization applied according to parameters
        - List[str]: A comprehensive list of human-readable descriptions of all
          changes made during the repair process, including specific modifications,
          insertions, and normalizations for transparency and debugging
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

    Parameters
    ----------
    text : str
        The markdown or text content to process. Can include multiple code blocks
        with various issues such as unclosed fences, inconsistent fence lengths,
        or missing language tags. The function processes the entire document.
    default_lang : Optional[str], default=None
        The default language tag to apply when no language can be detected
        automatically and no existing language tag is present. If None,
        code blocks without detectable languages will remain untagged.
        Common values include "python", "javascript", "bash", "sql", etc.
    keep_fence_char : bool, default=True
        Whether to preserve the original fence character type (backticks or tildes)
        found in each code block. If True, maintains the original character choice.
        If False, standardizes all fences to use backticks (```), providing
        consistency across the document.

    Returns
    -------
    Tuple[str, List[str]]
        A tuple containing two elements:
        - str: The processed markdown content with all code fence issues resolved
          and standardization applied according to parameters
        - List[str]: A comprehensive list of human-readable descriptions of all
          changes made during the repair process, including specific modifications,
          insertions, and normalizations for transparency and debugging
    """
    
    ok, issues = validate_code_fences(text)
    changes: List[str] = []
    if not ok:
        fixed, changes = fix_code_fences(text, default_lang=default_lang, keep_fence_char=keep_fence_char)
        ok2, issues2 = validate_code_fences(fixed)
        return fixed, (issues + changes + (["Still invalid after fix"] if not ok2 else []))
    fixed, changes = fix_code_fences(text, default_lang=default_lang, keep_fence_char=keep_fence_char)
    return fixed, changes

