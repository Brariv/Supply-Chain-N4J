from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen

class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Dashboard")),
            ListItem(Label("Settings")),
            ListItem(Label("Reports")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).renderable
        if label == "Quit":
            self.app.exit()
        else:
            self.app.push_screen(InfoScreen(f"You selected: {label}"))

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

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

if __name__ == "__main__":
    MyApp().run()