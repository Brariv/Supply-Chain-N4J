from pathlib import Path
import sys

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical

# Allow running this file directly with `python FrontEnd/Base.py`
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Revisar.login import login, dealership_login, driver
from UserUI import MenuScreen as UserMenuScreen
from DealershipUI import MenuScreen as DealerMenuScreen


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
        email = self.query_one("#name", Input).value
        password = self.query_one("#password", Input).value
        result = self.query_one("#result", Static)

        if event.button.id == "submit":
            if email and password:
                customer = login(driver, email, password)
                if customer:
                    self.app.customer_id = customer["customerId"]
                    self.app.switch_screen(UserMenuScreen())
                else:
                    result.update("✗ Invalid email or password")
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
            yield Input(placeholder="Enter the dealership name...", id="name")
            yield Label("Password:")
            yield Input(placeholder="Enter the dealership password...", id="password", password=True)
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
                dealership = dealership_login(driver, name, password)
                if dealership:
                    self.app.dealership_id = dealership["dealershipId"]
                    self.app.switch_screen(DealerMenuScreen())
                else:
                    result.update("✗ Invalid name or password")
            else:
                result.update("✗ Please fill in all fields")
        elif event.button.id == "clear":
            self.query_one("#name", Input).value = ""
            self.query_one("#password", Input).value = ""
            result.update("")

class MyApp(App):
    def __init__(self):
        super().__init__()
        self.customer_id: int = 0
        self.dealership_id: int = 0

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

MyApp().run()