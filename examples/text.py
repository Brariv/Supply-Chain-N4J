from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical

class FormApp(App):
    CSS = """
    Vertical { padding: 1 2; }
    Input { margin-bottom: 1; }
    #result { color: green; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Name:")
            yield Input(placeholder="Enter your name...", id="name")
            yield Label("Email:")
            yield Input(placeholder="Enter your email...", id="email")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Static("", id="result")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        name = self.query_one("#name", Input).value
        email = self.query_one("#email", Input).value
        result = self.query_one("#result", Static)

        if event.button.id == "submit":
            if name and email:
                result.update(f"✓ Submitted: {name} <{email}>")
            else:
                result.update("✗ Please fill in all fields")
        elif event.button.id == "clear":
            self.query_one("#name", Input).value = ""
            self.query_one("#email", Input).value = ""
            result.update("")

if __name__ == "__main__":
    FormApp().run()