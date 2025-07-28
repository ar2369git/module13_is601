
import pytest

@pytest.mark.e2e
def test_homepage_and_operations(page):
    # Navigate to the form
    page.goto("http://127.0.0.1:8000")
    # Check header
    assert page.inner_text("h1") == "Hello World"

    # helper to run an operation and check result text
    def do_op(op_button_text, a, b, expected):
        page.fill("#a", str(a))
        page.fill("#b", str(b))
        page.click(f'button:text("{op_button_text}")')
        # wait until the result DIV actually gets the text
        page.wait_for_selector(f"#result:has-text('{expected}')")
        assert page.inner_text("#result") == expected
    do_op("Add", 2, 3, "Calculation Result: 5")
    do_op("Subtract", 10, 4, "Calculation Result: 6")
    do_op("Multiply", 6, 7, "Calculation Result: 42")
    do_op("Divide", 9, 3, "Calculation Result: 3")
    do_op("Divide", 5, 0, "Error: Cannot divide by zero!")
