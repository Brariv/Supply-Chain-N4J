from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical

CarsExample = [
    {"make": "Toyota", "model": "Camry", "year": 2020},
    {"make": "Honda", "model": "Civic", "year": 2019},
    {"make": "Ford", "model": "Mustang", "year": 2021},
    {"make": "Tesla", "model": "Model 3", "year": 2022},
    {"make": "Chevrolet", "model": "Impala", "year": 2018},
    {"make": "BMW", "model": "3 Series", "year": 2020},
    {"make": "Audi", "model": "A4", "year": 2019},
    {"make": "Mercedes-Benz", "model": "C-Class", "year": 2021},
]

class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Visit DealerShip")),
            ListItem(Label("Show My Cars")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        if label == "Quit":
            self.app.exit()
        if label == "Visit DealerShip":
            self.app.push_screen(ShowRoomScreen())
        if label == "Show My Cars":
            self.app.push_screen(ShowCarsScreen())
        

class ShowCarsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Here are your cars!")
        yield Label("\nPress Escape to go back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()



class ShowRoomScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Welcome to the showroom!")
        yield ListView(
            *[ListItem(Label(f"{car['year']} {car['make']} {car['model']}")) for car in CarsExample]
        )
        
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        car_info = event.item.query_one(Label).render()
        self.app.push_screen(InfoScreen(f"You selected: {car_info}"))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

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