def run(input_text: str) -> str:
    cleaned_input = " ".join(input_text.split())
    return f"{{module_name}} received: {cleaned_input}"
