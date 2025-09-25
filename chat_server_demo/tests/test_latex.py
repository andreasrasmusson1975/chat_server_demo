import pytest
from chat_server_demo.helper_functionality.latex import fix_latex_delimiters


def test_balanced_inline_math_passes():
    text = "This is $x+1$ inline math."
    fixed, edits = fix_latex_delimiters(text)
    assert fixed == text
    assert edits == []  # no changes expected

def test_unclosed_inline_math_gets_closed():
    text = "Equation: $x+1"
    fixed, edits = fix_latex_delimiters(text)
    assert "$x+1$" in fixed
    assert any("Inserted missing closer" in e.reason for e in edits)

def test_mismatched_delimiters_repaired():
    text = r"\(x+1\]"
    fixed, edits = fix_latex_delimiters(text)
    assert r"\(x+1\)" in fixed
    assert any("Mismatched closer" in e.reason for e in edits)

def test_currency_not_treated_as_math():
    text = "The price is $12.50 today."
    fixed, edits = fix_latex_delimiters(text)
    assert fixed == text  # untouched
    assert edits == []

def test_protected_code_fence_ignored():
    text = "```python\nx = '$notmath'\n```"
    fixed, edits = fix_latex_delimiters(text)
    assert "'$notmath'" in fixed  # inside code fence unchanged
    assert edits == []

def test_auto_close_on_newline():
    text = "Here is math: $x+1\nnext line"
    fixed, edits = fix_latex_delimiters(text, close_on_newline=True)
    assert "$x+1$" in fixed
    assert "next line" in fixed
    assert any("at end of line" in e.reason for e in edits)

def test_align_environment_normalized():
    text = r"""\begin{align}
    x &= y
    \end{align}"""
    fixed, edits = fix_latex_delimiters(text)
    assert r"\begin{aligned}" in fixed
    assert fixed.strip().startswith("$$")
    assert fixed.strip().endswith("$$")
