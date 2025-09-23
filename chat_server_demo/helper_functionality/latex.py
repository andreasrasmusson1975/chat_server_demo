"""
LaTeX Math Delimiter Normalization and Repair Module

This module provides utilities for repairing and normalizing LaTeX math delimiters
in user-generated or LLM-generated text. It ensures proper balancing and formatting
of inline and display math environments, while protecting code, comments, and other
non-math regions from unintended modifications.

Key Features
------------
- Balances LaTeX math delimiters such as `$`, `$$`, `\(`, `\)`, `\[`, and `\]`
- Converts mismatched closers (e.g., `\( ... \]` -> `\( ... \)`)
- Closes any still-open math delimiters at the end of lines or the document
- Skips protected regions like code fences, inline code, comments, and verbatim environments
- Respects escaped delimiters (e.g., `\\$`, `\\[`)
- Heuristically distinguishes between math and currency usages of `$`
- Returns both the fixed text and a list of edits describing all changes

Architecture
------------
The module is built around the `LaTeXFixer` class, which encapsulates the logic for
scanning and repairing LaTeX math delimiters. It uses regular expressions to identify
and process delimiters, while maintaining a list of edits for transparency and debugging.

Classes
-------
- `Edit`: Represents a single edit operation applied to the text during delimiter fixing
- `LaTeXFixer`: Repairs and normalizes LaTeX math delimiters with configurable options

Dependencies
------------
- `re`: For regular expression operations
- `dataclasses`: For the `Edit` class
- `typing`: For type hints and improved code clarity

Author
------
Andreas Rasmusson
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal

@dataclass
class Edit:
    """
    Represents a single edit operation applied to a LaTeX or Markdown string during delimiter fixing.

    Attributes
    ----------
    kind : Literal["insert", "replace", "delete"]
        The type of edit operation: 'insert', 'replace', or 'delete'.
    pos : int
        The index in the original text where the edit applies (best-effort for inserts).
    before : str
        The substring in the original text before the edit (empty for insert).
    after : str
        The substring to replace with (empty for delete).
    reason : str
        Human-readable explanation for why this edit was made.
    """
    kind: Literal["insert", "replace", "delete"]
    pos: int               # index in original text where edit refers (best-effort for inserts)
    before: str
    after: str
    reason: str

class LaTeXFixer:
    """
    Repairs and normalizes LaTeX math delimiters in LLM-generated or user-provided text.

    This class scans text for common LaTeX math delimiter issues and applies fixes to ensure proper
    balancing and formatting of inline and display math environments. It protects code, comments,
    and verbatim regions, and heuristically distinguishes between math and currency usages of '$'.

    Features
    --------
    - Balances $, $$, \(, \), \[, \] math delimiters (no nesting of math).
    - Converts mismatched closers (e.g., \( ... \] -> \( ... \)).
    - Closes any still-open math at the end of lines or document.
    - Skips protected regions: code fences, inline code, comments, verbatim/minted/lstlisting environments, and \verb.
    - Respects escapes (e.g., \\$, \\\[).
    - Heuristically ignores currency-like $12.50 to avoid wrapping as math.
    - Returns both the fixed text and a list of Edit records describing all changes.

    Usage
    -----
    Instantiate with optional close_on_newline argument, then call fix(text) to repair delimiters.

    Parameters
    ----------
    close_on_newline : bool, optional
        If True (default), auto-close any open math at each newline.

    Returns
    -------
    Tuple[str, List[Edit]]
        The fixed text and a list of Edit records describing all changes made.
    """
    

    _code_fence = re.compile(r"```.*?```", re.DOTALL)
    _inline_code = re.compile(r"`[^`\n]*`")
    _comment = re.compile(r"(?m)%[^\n]*$")
    _verb_env_open = re.compile(r"\\begin\{(verbatim|lstlisting|minted)(?:\*?)\b[^\}]*\}")
    _verb_env_close_tmpl = r"\\end\{\1\}"
    _verb_inline = re.compile(r"\\verb(?P<d>[^A-Za-z0-9\s])(?:.*?)(?P=d)")  # \verb|...|  \verb+...+
    _escaped_backslash = re.compile(r"(?:^|[^\\])((?:\\\\)*)\\$")  # helper: odd/even backslashes end of prefix

    # Delimiter tokens; longest-first is important
    _tokens = ("\\[", "\\]", "\\(", "\\)", "$$", "$")
    _openers = {"\\[": "\\[", "\\(": "\\(", "$$": "$$", "$": "$"}
    _closers = {"\\]": "\\]", "\\)": "\\)", "$$": "$$", "$": "$"}
    _matching = {"\\[": "\\]", "\\(": "\\)", "$$": "$$", "$": "$"}
    _closing_of = {"\\]": "\\[", "\\)": "\\(", "$$": "$$", "$": "$"}

    def __init__(self, *, close_on_newline: bool = True):
        self.close_on_newline = close_on_newline

    # ---------- public API ----------

    def fix(self, text: str) -> Tuple[str, List[Edit]]:
        """
        Scan and repair LaTeX math delimiters in the given text.

        This method processes the input string, fixing common delimiter issues such as unbalanced or mismatched
        math environments ($, $$, \(, \), \[, \]), and returns the corrected text along with a list of all
        edit operations performed. Protected regions (code, comments, verbatim, etc.) are left unchanged.

        Parameters
        ----------
        text : str
            The input string containing LaTeX or Markdown with possible math delimiter issues.

        Returns
        -------
        Tuple[str, List[Edit]]
            A tuple containing the fixed text and a list of Edit records describing all changes made.

        Notes
        -----
        - Does not attempt to fix general LaTeX syntax errors, only math delimiter issues.
        - Respects protected regions and escapes.
        - Designed for use with LLM-generated or user-provided Markdown/LaTeX content.
        """
        protected = self._protected_spans(text)
        return self._scan_and_fix(text, protected)

    # ---------- protected spans ----------

    def _protected_spans(self, s: str) -> List[Tuple[int, int]]:
        """
        Identify and return spans of text that should be protected from delimiter fixing.

        This method scans the input string for regions that should not be altered by math delimiter
        repairs, such as code fences, inline code, LaTeX comments, verbatim-like environments, and
        inline \verb commands. Overlapping and adjacent spans are merged for efficiency.

        Parameters
        ----------
        s : str
            The input string to scan for protected regions.

        Returns
        -------
        List[Tuple[int, int]]
            A list of (start, end) index tuples representing protected spans in the input string.

        Notes
        -----
        - Protected regions are left unchanged by delimiter fixing logic.
        - Merges overlapping or adjacent spans for optimal coverage.
        """
        spans = []
        # code fences
        for m in self._code_fence.finditer(s):
            spans.append((m.start(), m.end()))
        # inline code
        for m in self._inline_code.finditer(s):
            spans.append((m.start(), m.end()))
        # comments (to end of line)
        for m in self._comment.finditer(s):
            spans.append((m.start(), m.end()))
        # verbatim-like envs
        for m in self._verb_env_open.finditer(s):
            start = m.start()
            name = m.group(1)
            # find the matching \end{name} after this
            end_pat = re.compile(rf"\\end\{{{re.escape(name)}\}}")
            close = end_pat.search(s, m.end())
            end = (close.end() if close else len(s))
            spans.append((start, end))
        # \verb?…?
        for m in self._verb_inline.finditer(s):
            spans.append((m.start(), m.end()))
        # merge overlaps
        spans.sort()
        merged = []
        for st, en in spans:
            if not merged or st > merged[-1][1]:
                merged.append((st, en))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], en))
        return merged

    def _in_protected(self, i: int, spans: List[Tuple[int, int]]) -> bool:
        """
        Determine whether a given index falls within any protected span.

        This method checks if the character position `i` is inside any of the (start, end)
        intervals in the provided list of protected spans. Used to avoid modifying code,
        comments, or verbatim regions during delimiter fixing.

        Parameters
        ----------
        i : int
            The character index to check.
        spans : List[Tuple[int, int]]
            A list of (start, end) index tuples representing protected regions.

        Returns
        -------
        bool
            True if the index is within any protected span, False otherwise.

        Notes
        -----
        - Uses a linear scan; efficient for small numbers of spans.
        - For large numbers of spans, a binary search could be used for optimization.
        """
        for st, en in spans:
            if st <= i < en:
                return True
        return False

    # ---------- helpers ----------

    @staticmethod
    def _count_trailing_backslashes(prefix: str) -> int:
        """
        Count the number of consecutive trailing backslashes in a string.

        This helper is used to determine whether a delimiter or special character is escaped
        by an odd number of backslashes immediately preceding it.

        Parameters
        ----------
        prefix : str
            The string to scan (typically the substring before a delimiter).

        Returns
        -------
        int
            The number of consecutive trailing backslashes at the end of the string.

        Notes
        -----
        - Used to distinguish between escaped and unescaped LaTeX/math delimiters.
        """
        cnt = 0
        for ch in reversed(prefix):
            if ch == '\\':
                cnt += 1
            else:
                break
        return cnt

    @staticmethod
    def _looks_like_currency(s: str, i: int) -> bool:
        """
        Heuristically determine if a dollar sign at position i in a string represents currency.

        This method checks if a '$' is followed by a number (optionally with commas or decimals),
        and is not immediately followed by another '$' (which would indicate math mode).
        Used to avoid misinterpreting currency as LaTeX math delimiters.

        Parameters
        ----------
        s : str
            The string to scan.
        i : int
            The index of the '$' character to check.

        Returns
        -------
        bool
            True if the '$' at position i is likely currency, False if it is likely a math delimiter.

        Notes
        -----
        - Recognizes patterns like $12, $12.50, $1,234.56 as currency.
        - If another '$' immediately follows the number (e.g., $5$), it is treated as math.
        """
        m = re.match(r"\$(\d{1,3}(?:[.,]\d{3})*|\d+)(?:[.,]\d+)?", s[i:])
        if not m:
            return False
        # if another $ is immediately after the number (like $5$), it's likely math
        after = i + len(m.group(0))
        if after < len(s) and s[after] == "$":
            return False
        return True

    # ---------- core scan ----------

    def _scan_and_fix(self, s: str, protected: List[Tuple[int, int]]) -> Tuple[str, List[Edit]]:
        """
        Core algorithm for scanning and repairing LaTeX math delimiters in text.

        This method iterates through the input string, skipping protected regions, and applies
        logic to balance, close, or correct math delimiters ($, $$, \(, \), \[, \]). It handles
        escapes, currency heuristics, and produces a list of all edit operations performed.

        Parameters
        ----------
        s : str
            The input string to scan and fix.
        protected : List[Tuple[int, int]]
            List of (start, end) index tuples representing protected regions to skip.

        Returns
        -------
        Tuple[str, List[Edit]]
            The fixed string and a list of Edit records describing all changes made.

        Notes
        -----
        - This is the main workhorse for delimiter repair, called by fix().
        - Handles stray, mismatched, and missing delimiters, as well as protected regions.
        - Maintains a stack to track open math environments.
        """
        out = []
        edits: List[Edit] = []
        i = 0
        n = len(s)
        # stack holds tuples: (opener_token, output_index_snapshot, original_index)
        stack: List[Tuple[str, int, int]] = []

        def insert_closer(tok_open: str, where_desc: str, before_newline: bool = False):
            closer = self._matching[tok_open]
            edits.append(Edit(kind="insert",
                              pos=i, before="", after=closer,
                              reason=f"Inserted missing closer {closer} for {tok_open} {where_desc}"))
            out.append(closer)

        while i < n:
            if self._in_protected(i, protected):
                # copy protected region verbatim
                # find which span we’re in
                for st, en in protected:
                    if st <= i < en:
                        out.append(s[i:en])
                        i = en
                        break
                continue

            ch = s[i]

            # Auto-close at newline if requested
            if ch == "\n" and self.close_on_newline and stack:
                # Close all currently open math before newline
                # (order: close last-opened first)
                while stack:
                    tok_open, _, _ = stack.pop()
                    insert_closer(tok_open, "at end of line", before_newline=True)
                out.append(ch)
                i += 1
                continue

            # Try to match any token (longest-first)
            tok: Optional[str] = None
            for t in self._tokens:
                if s.startswith(t, i):
                    tok = t
                    break

            if tok is None:
                out.append(ch)
                i += 1
                continue

            # Handle escapes like \\$ or \\\( etc.: if an odd number of backslashes immediately precedes, skip
            bs = self._count_trailing_backslashes(s[:i])
            if bs % 2 == 1:
                # escaped token: treat as plain text
                out.append(tok)
                i += len(tok)
                continue

            # Heuristic: currency $12.50 -> don’t treat as math opener
            if tok == "$" and not stack and self._looks_like_currency(s, i):
                out.append("$")
                i += 1
                continue

            # Decide opener/closer/nature
            if tok in self._openers and tok not in self._closers:
                is_opener = True
                is_closer = False
            elif tok in self._closers and tok not in self._openers:
                is_opener = False
                is_closer = True
            else:
                # $, $$ act as both: if stack top is same, it's closer; else opener
                if stack and stack[-1][0] == tok:
                    is_opener, is_closer = False, True
                else:
                    is_opener, is_closer = True, False

            if is_opener:
                # If math is already open, this likely indicates a missing closer before.
                if stack:
                    # insert a closer for current top before opening new one
                    open_tok, _, _ = stack.pop()
                    insert_closer(open_tok, "before opening a new math block")
                # push new opener
                stack.append((tok, len(out), i))
                out.append(tok)
                i += len(tok)
                continue

            # is_closer
            if not stack:
                # stray closer; delete it (safer than turning it into opener)
                edits.append(Edit(kind="delete", pos=i, before=tok, after="",
                                  reason=f"Stray closer {tok} removed"))
                i += len(tok)
                continue

            open_tok, _, open_at = stack[-1]
            want_closer = self._matching[open_tok]
            if tok == want_closer:
                # perfect match
                stack.pop()
                out.append(tok)
                i += len(tok)
                continue
            else:
                # mismatched closer: replace with the right one
                edits.append(Edit(kind="replace", pos=i, before=tok, after=want_closer,
                                  reason=f"Mismatched closer: {tok} -> {want_closer} for opener {open_tok}"))
                stack.pop()
                out.append(want_closer)
                i += len(tok)
                continue

        # End of text: close any remaining math
        while stack:
            tok_open, _, _ = stack.pop()
            closer = self._matching[tok_open]
            edits.append(Edit(kind="insert", pos=n, before="", after=closer,
                              reason=f"Inserted missing closer {closer} at end of document"))
            out.append(closer)

        return ("".join(out), edits)
        

def fix_align_environments(text: str) -> str:
    """
    Normalize LaTeX align-family environments for KaTeX/Markdown rendering.

    Converts any of:
        \begin{align}...\end{align}
        \begin{align*}...\end{align*}
        \begin{aligned}...\end{aligned}

    into:
        $$
        \begin{aligned}
          ...
        \end{aligned}
        $$

    Fixes applied:
    - Replace align/align* with aligned.
    - Wrap in $$ ... $$ for display math.
    - Remove redundant dollar signs ($$ or $$$$).
    - Insert line breaks (\\) between equations if missing.
    """
    def replacer(match):
        env = match.group(1)   # align, align*, or aligned
        content = match.group(2)

        # Remove stray '$' (common in LLM output like $$$$)
        content = content.replace("$$$$", "").replace("$$", "")

        # If multiple equations are jammed together, try to insert proper line breaks
        content = re.sub(r"\)\s*(\\\w+)", r") \\\\\1", content)

        # Always normalize to "aligned"
        return "$$\n\\begin{aligned}\n" + content.strip() + "\n\\end{aligned}\n$$"

    pattern = re.compile(r"\\begin{(align\*?|aligned)}(.*?)\\end{\1}", re.DOTALL)
    return pattern.sub(replacer, text)





def fix_latex_delimiters(
    text: str,
    close_on_newline: bool = True
) -> Tuple[str, List[Edit]]:
    """
    Convenience wrapper to repair LaTeX math delimiters and align environments in Markdown or LaTeX text.

    This function uses LaTeXFixer to scan and fix common math delimiter issues (unbalanced, mismatched, or
    missing $/$$/\(\)/\[\] delimiters) and then rewrites any \begin{align}...\end{align} blocks to
    $$...$$ with \begin{aligned}...\end{aligned} for better Markdown rendering.

    Parameters
    ----------
    text : str
        Input string containing possibly broken LaTeX or Markdown with math.
    close_on_newline : bool, optional
        If True (default), auto-close any open math at each newline.

    Returns
    -------
    Tuple[str, List[Edit]]
        The fixed text and a list of Edit records describing all changes made.

    Notes
    -----
    - Applies both delimiter repair and align-to-aligned conversion for Markdown math compatibility.
    - Designed for use with LLM-generated or user-provided Markdown/LaTeX content.
    """
    fixer = LaTeXFixer(close_on_newline=close_on_newline)
    fixed, edits = fixer.fix(text)
    fixed = fix_align_environments(fixed)
    return fixed, edits
