from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical
import random

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

WarehousesExample = [
    {"name": "Warehouse A", "location": "City X"},
    {"name": "Warehouse B", "location": "City Y"},
    {"name": "Warehouse C", "location": "City Z"},
    {"name": "Warehouse D", "location": "City W"},
]

DealershipsExample = [
    {"name": "Dealership 1", "location": "City A"},
    {"name": "Dealership 2", "location": "City B"},
    {"name": "Dealership 3", "location": "City C"},
    {"name": "Dealership 4", "location": "City D"},
]

class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Inventory")),
            ListItem(Label("Car Management")),
            ListItem(Label("Discount Management")),
            ListItem(Label("Transaction Reports")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        if label == "Quit":
            self.app.exit()
        if label == "Inventory":
            self.app.push_screen(InventoryScreen())
        if label == "Showroom Management":
            self.app.push_screen(CarManagementScreen())
        if label == "Discount Management":
            self.app.push_screen(DiscountManagementScreen())
        if label == "Back Order":
            self.app.push_screen(BackOrderScreen())
        if label == "Transaction Reports":
            self.app.push_screen(TransactionReportsScreen())
        # else:
        #     self.app.push_screen(InfoScreen(f"You selected: {label}"))

#     manufacturer_id: str,
#     body_type: str,           # SUV | Sedan | Pickup
#     fuel_type: str,           # Electric | Diesel | Gas
#     model: str,
#     brand: str,
#     color: str,
#     year: int,
#     plate: str,
#     group: str,
#     special_order: bool,
#     destination_country: str,
class BackOrderScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Create Back Order")  
        yield Header(show_clock=True)
        with Vertical():
            
        



        yield Label("\nPress Escape to go back")

    
    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class InventoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Current Inventory")
        yield ListView(
            *[ListItem(Label(f"{car['year']} {car['make']} {car['model']}")) for car in CarsExample]
        )
        yield Label("\nPress Escape to go back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class CarInfoScreen(Screen):
    def __init__(self, car_info: str):
        super().__init__()
        self.car_info = car_info
        self.price = random.randint(10000, 50000)
        self.discount = random.randint(0, 5000)

    def compose(self) -> ComposeResult:
        yield Label(f"You selected: {self.car_info}")
        yield Label(f"Price: ${self.price}")
        yield Label(f"Discount: ${self.discount}")
        yield Label("\nPress Escape to go back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

# def ManageCarScreen(Screen):


class CarManagementScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Car Management")
        yield Header(show_clock=True)
        yield ListView(
            ListItem(Label("Change Car Status")),
            ListItem(Label("Ship New Car")),
            ListItem(Label("Order New Car")),
            ListItem(Label("Custom Orders")),
        )
        yield Label("\nPress Escape to go back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()
        

class DiscountManagementScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Discount Management")
        yield Header(show_clock=True)
        yield ListView(
            ListItem(Label("New Discount")),
            ListItem(Label("Delete Discount")),
        )
        yield Label("\nPress Escape to go back")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        if label == "New Discount":
            self.app.push_screen(NewDiscountcreen())
        if label == "Delete Discount":
            self.app.push_screen(DeleteDiscountScreen())
        # else:
        #     self.app.push_screen(InfoScreen(f"You selected: {label}"))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class NewDiscountcreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("New Discount")
        yield Header(show_clock=True)
        with Vertical():
            yield Label("Discount Percentage:")
            yield Input(placeholder="Enter discount percentage...", id="discount")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Static("", id="result")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class DeleteDiscountScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Delete Discount")
        yield Header(show_clock=True)
        with Vertical():
            yield Label("Discount ID:")
            yield Input(placeholder="Enter discount ID...", id="discount_id")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Static("", id="result")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()



# class ShowCarsScreen(Screen):
#     def compose(self) -> ComposeResult:
#         yield Label("Here are your cars!")
#         yield Label("\nPress Escape to go back")

#     def on_key(self, event) -> None:
#         if event.key == "escape":
#             self.app.pop_screen()



# class ShowRoomScreen(Screen):
#     def compose(self) -> ComposeResult:
#         yield Header(show_clock=True)
#         yield Label("Welcome to the showroom!")
#         yield ListView(
#             *[ListItem(Label(f"{car['year']} {car['make']} {car['model']}")) for car in CarsExample]
#         )
        
#         yield Label("\nPress Escape to go back")
#         yield Footer()

#     def on_list_view_selected(self, event: ListView.Selected) -> None:
#         car_info = event.item.query_one(Label).render()
#         self.app.push_screen(NegotiationScreen(car_info))

#     def on_key(self, event) -> None:
#         if event.key == "escape":
#             self.app.pop_screen()

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

# class NegotiationScreen(Screen):
#     def __init__(self, car_info: str):
#         super().__init__()
#         self.car_info = car_info
#         self.price = random.randint(10000, 50000)
#         self.accepted_price = random.uniform(0.05, 0.15)  
#         self.offers = []

#     def compose(self) -> ComposeResult:
#         yield Label(f"You selected: {self.car_info}")
#         yield Label(f"The MSRP is: ${self.price}")
#         yield Label("Offer:")
#         yield Input(placeholder="Enter your offer...", id="offer")
#         yield Button("Submit", id="submit", variant="primary")
#         yield Button("Clear", id="clear", variant="default")
#         yield Static("", id="result")
#         yield Static("", id="offer_history")
    
#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         offer = self.query_one("#offer", Input).value
#         result = self.query_one("#result", Static)
#         offer_history = self.query_one("#offer_history", Static)

#         if event.button.id == "submit":
#             self.offers.append(offer)
#             if offer:
#                 offer = int(offer)
#                 if offer >= self.price * (1 - self.accepted_price):
#                     result.update(f"✓ Offer accepted: ${offer}")
#                     offer_history.update("Offer History:\n" + "\n".join(self.offers))
#                 else:
#                     result.update(f"✗ Offer too low: ${offer}")
#                     offer_history.update("Offer History:\n" + "\n".join(self.offers))
#             else:
#                 result.update("✗ Please enter an offer")
#         elif event.button.id == "clear":
#             self.query_one("#offer", Input).value = ""
#             result.update("")

#     def on_key(self, event) -> None:
#         if event.key == "escape":
#             self.app.pop_screen()


class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

if __name__ == "__main__":
    MyApp().run()