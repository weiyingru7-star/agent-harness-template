def run(input_text: str) -> str:
    cleaned_input = " ".join(input_text.split())
    return f"example_agent received: {cleaned_input}"
