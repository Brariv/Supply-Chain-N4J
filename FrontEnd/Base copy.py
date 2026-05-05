from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical

from Revisar.login import login, dealership_login


class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("DealerShip")),
            ListItem(Label("User")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        if label == "Quit":
            self.app.exit()
        if label == "User":
            self.app.push_screen(UserLogin())
        if label == "DealerShip":
            self.app.push_screen(DealershipLogin())
class InfoScreen(Screen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Label(self.message)
        yield Label("\nPress Escape to go back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class UserLogin(Screen):
    CSS = """
    Vertical { padding: 1 2; }
    Input { margin-bottom: 1; }
    #result { color: green; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Email:")
            yield Input(placeholder="Enter your email...", id="name")
            yield Label("Password:")
            yield Input(placeholder="Enter your password...", id="password", password=True)
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Label("\nPress Escape to go back")
            yield Static("", id="result")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        name = self.query_one("#name", Input).value
        password = self.query_one("#password", Input).value
        result = self.query_one("#result", Static)

        if event.button.id == "submit":
            if name and password:
                result.update(f"✓ Submitted: {name} <{password}>")
            else:
                result.update("✗ Please fill in all fields")
        elif event.button.id == "clear":
            self.query_one("#name", Input).value = ""
            self.query_one("#password", Input).value = ""
            result.update("")


class DealershipLogin(Screen):
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
            yield Label("Password:")
            yield Input(placeholder="Enter your password...", id="password", password=True)
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Label("\nPress Escape to go back")
            yield Static("", id="result")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        name = self.query_one("#name", Input).value
        password = self.query_one("#password", Input).value
        result = self.query_one("#result", Static)

        if event.button.id == "submit":
            if name and password:
                result.update(f"✓ Submitted: {name} <{password}>")
            else:
                result.update("✗ Please fill in all fields")
        elif event.button.id == "clear":
            self.query_one("#name", Input).value = ""
            self.query_one("#password", Input).value = ""
            result.update("")

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

if __name__ == "__main__":
    MyApp().run()