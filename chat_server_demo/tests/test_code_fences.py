import pytest
from chat_server_demo.helper_functionality.code_fences import ensure_fenced_code

def test_valid_fence_passes():
    text = """```python
    print("hello")
    ```"""
    fixed, changes = ensure_fenced_code(text)
    assert "print" in fixed
    assert changes == []  # no changes needed

def test_unclosed_fence_fixed():
    text = """```python
    print("oops")"""
    fixed, changes = ensure_fenced_code(text)
    assert fixed.strip().endswith("```")
    assert any("Inserted missing closing fence" in c for c in changes)

def test_missing_language_tag_guessed():
    text = """```
    def foo():
        return 1
    ```"""
    fixed, changes = ensure_fenced_code(text)
    assert "python" in fixed
    assert any("Added guessed language tag" in c for c in changes)

def test_missing_language_tag_with_default():
    text = """```
    some plain code
    ```"""
    fixed, changes = ensure_fenced_code(text, default_lang="bash")
    assert "bash" in fixed
    assert any("Added default language tag" in c for c in changes)

def test_adjust_fence_length_inside_code():
    text = """```
    print("``` inside code")
    ```"""
    fixed, changes = ensure_fenced_code(text)

    # Get the opening fence (first non-empty line)
    first_line = fixed.splitlines()[0]

    # Ensure the fence is longer than 3 backticks
    assert first_line.startswith("`")
    assert len(first_line.split()[0]) > 3

    # Ensure the change log mentions the adjustment
    assert any("Adjusted fence length" in c for c in changes)

def test_stray_closing_fence():
    text = "some text\n```\nprint('x')\n```\n```"
    fixed, changes = ensure_fenced_code(text)

    # The stray fence may still remain in the normalized output,
    # but the repair process should have logged it as an issue/change.
    assert any(
        "Closing fence without opening" in c
        or "Inserted missing closing fence" in c
        for c in changes
    )

    # Ensure the original code block is still intact
    assert "print('x')" in fixed


def test_section_boundary_closes_fence():
    text = """```python
    print("hello")
    ### Revised Answer
    some text"""
    fixed, changes = ensure_fenced_code(text)

    # Allow both ```python and ``` python
    assert fixed.lstrip().startswith("```")
    assert "python" in fixed.splitlines()[0].lower()

    # Section boundary should have forced fence closure
    assert "### Revised Answer" in fixed
    assert any(
        "Inserted missing closing fence before heading" in c
        for c in changes
    )

