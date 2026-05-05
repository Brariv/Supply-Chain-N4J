from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual.containers import Vertical, Horizontal
import random
import time



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
            ListItem(Label("Account")),
            ListItem(Label("Visit History")),
            ListItem(Label("Custom Car Status")),
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
        if label == "Account":
            self.app.push_screen(AccountManagmentScreen())
        if label == "Visit History":
            self.app.push_screen(VisitHistoryScreen(["Visit 1", "Visit 2", "Visit 3"]))
        if label == "Custom Car Status":
            self.app.push_screen(CustomCarStatusScreen(["Car 1", "Car 2", "Car 3"]))


class ShowCarsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Here are your cars!")
        yield ListView(
            *[ListItem(Label(f"{car['year']} {car['make']} {car['model']}")) for car in CarsExample]
        )
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
        self.app.push_screen(NegotiationScreen(car_info))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.push_screen(RateVisitScreen())

RATING_LABELS = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent"}

class RateVisitScreen(Screen):
    CSS = """
    RateVisitScreen Label#rate_title {
        text-align: center;
        width: 100%;
        padding: 1 0;
    }
    RateVisitScreen #stars_row {
        align: center middle;
        height: 10;
        padding: 1 0;
    }
    RateVisitScreen #stars_row Button {
        padding: 0 1;
        margin: 0 1;
        background: transparent;
        border: none;
        color: $warning;
    }
    RateVisitScreen #rating_label {
        text-align: center;
        width: 100%;
        height: 1;
        color: $warning;
    }
    RateVisitScreen #rating_display {
        text-align: center;
        width: 100%;
        height: 1;
        color: $error;
    }
    RateVisitScreen #submit {
        margin: 1 0;
        align-horizontal: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.rating = 0

    def compose(self):
        yield Header()
        yield Label("How was your visit?", id="rate_title")
        with Horizontal(id="stars_row"):
            for i in range(1, 6):
                yield Button("☆", id=f"star_{i}")
        yield Static("", id="rating_label")
        yield Static("", id="rating_display")
        yield Button("Submit Rating", id="submit", variant="primary")
        yield Footer()

    def _refresh_stars(self):
        for i in range(1, 6):
            self.query_one(f"#star_{i}", Button).label = "★" if i <= self.rating else "☆"
        self.query_one("#rating_label", Static).update(RATING_LABELS.get(self.rating, ""))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("star_"):
            self.rating = int(event.button.id[-1])
            self._refresh_stars()
            self.query_one("#rating_display", Static).update("")
        elif event.button.id == "submit":
            if self.rating > 0:
                self.app.push_screen(MenuScreen())
            else:
                self.query_one("#rating_display", Static).update("Please select a rating first.")

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

class NegotiationScreen(Screen):
    def __init__(self, car_info: str):
        super().__init__()
        self.car_info = car_info
        self.price = random.randint(10000, 50000)
        self.accepted_price = random.uniform(0.05, 0.15)  
        self.offers = []

    def compose(self) -> ComposeResult:
        yield Label(f"You selected: {self.car_info}")
        yield Label(f"The MSRP is: ${self.price}")
        with Vertical():
            yield Label("Offer:")
            yield Input(placeholder="Enter your offer...", id="offer")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
        yield Static("", id="result")
        yield Static("", id="offer_history")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        offer = self.query_one("#offer", Input).value
        result = self.query_one("#result", Static)
        offer_history = self.query_one("#offer_history", Static)

        if event.button.id == "submit":
            self.offers.append(offer)
            if offer:
                offer = int(offer)
                if offer >= self.price * (1 - self.accepted_price):
                    result.update(f"✓ Offer accepted: ${offer}")
                    offer_history.update("Offer History:\n" + "\n".join(self.offers))
                    self.app.push_screen(TransactionScreen(self.car_info, offer))
                else:
                    result.update(f"✗ Offer too low: ${offer}")
                    offer_history.update("Offer History:\n" + "\n".join(self.offers))
            else:
                result.update("✗ Please enter an offer")
        elif event.button.id == "clear":
            self.query_one("#offer", Input).value = ""
            result.update("")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()
    

class TransactionScreen(Screen):
    def __init__(self, car_info: str, agreed_price: int):
        super().__init__()
        self.car_info = car_info
        self.agreed_price = agreed_price

    def compose(self) -> ComposeResult:
        yield Label("Transaction Reports")
        yield Label(f"You agreed to buy {self.car_info} for ${self.agreed_price}")
        yield Label("\nPayment Options:")
        yield ListView(
            ListItem(Label("Credit Card")),
            ListItem(Label("Financing")),
            ListItem(Label("Bank Transfer")),
            ListItem(Label("Check")),
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_payment = event.item.query_one(Label).render()
        self.app.push_screen(PaymentScreen(selected_payment, self.agreed_price))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class PaymentScreen(Screen):
    def __init__(self, selected_payment: str, Aggreed_Price: int):
        super().__init__()
        self.selected_payment = selected_payment
        self.Aggreed_Price = Aggreed_Price

    def compose(self) -> ComposeResult:
        yield Label("Payment Options")
        if self.selected_payment == "Credit Card":
            yield Label("You selected Credit Card. Please enter your card details.")
            with Vertical():
                yield Label("Card Number:")
                yield Input(placeholder="Enter your card number...", id="card_number")
                yield Label("Expiration Date:")
                yield Input(placeholder="MM/YY", id="expiration_date")
                yield Label("CVV:")
                yield Input(placeholder="Enter CVV...", id="cvv", password=True)
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        elif self.selected_payment == "Financing":
            yield Label("You selected Financing. Please enter your financing details.")
            with Vertical():
                yield Label("Months to Pay:")
                yield Input(placeholder="Enter the number of months...", id="months")
                yield Button("Check Montly Payments", id="checkmp", variant="warning")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        elif self.selected_payment == "Bank Transfer":
            yield Label("You selected Bank Transfer. Please enter your bank details.")
            with Vertical():
                yield Label("Bank Name:")
                yield Input(placeholder="Enter your bank name...", id="bank_name")
                yield Label("Account Number:")
                yield Input(placeholder="Enter your account number...", id="account_number")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        elif self.selected_payment == "Check":
            yield Label("You selected Check. Please enter your check details.")
            with Vertical():
                yield Label("Check Number:")
                yield Input(placeholder="Enter your check number...", id="check_number")
                yield Label("Bank Name:")
                yield Input(placeholder="Enter your bank name...", id="bank_name_check")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        yield Label("", id="result")
        yield Label("", id="financing_result")
        yield Label("\nPress Escape to go back")
        yield Footer()

    

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result = self.query_one("#result", Label)
        if event.button.id == "submit":
            result.update(f"✓ {self.selected_payment} details submitted successfully!")
            time.sleep(2)  # Simulate processing time
            self.app.push_screen(RateVisitScreen())
        elif event.button.id == "clear":
            result.update("")
        elif event.button.id == "checkmp" and self.selected_payment == "Financing":
            months = self.query_one("#months", Input).value
            if months:
                financing_result = self.query_one("#financing_result", Label)
                financing_result.update(f"Financing for {months} months at ${self.Aggreed_Price / int(months):.2f} per month")
        

        
    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class CarStatusScreen(Screen):
    def __init__(self, cars: str):
        super().__init__()
        #options = [("First", 1), ("Second", 2)]
        self.cars = [(car, i) for i, car in enumerate(cars)]
        self.status = [""]

class VisitHistoryScreen(Screen):
    def __init__(self, visits: str):
        super().__init__()
        self.visits = [(visit, i) for i, visit in enumerate(visits)]
        self.status = [""]
    
    def compose(self) -> ComposeResult:
        yield Label("Visit History")
        yield ListView(
            *[ListItem(Label(f"{visit[0]}")) for visit in self.visits]
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        

class PastRatingScreen(Screen):
    def __init__(self, visit: str):
        super().__init__()
        self.visit = visit

    CSS = """
    RateVisitScreen Label#rate_title {
        text-align: center;
        width: 100%;
        padding: 1 0;
    }
    RateVisitScreen #stars_row {
        align: center middle;
        height: 10;
        padding: 1 0;
    }
    RateVisitScreen #stars_row Button {
        padding: 0 1;
        margin: 0 1;
        background: transparent;
        border: none;
        color: $warning;
    }
    RateVisitScreen #rating_label {
        text-align: center;
        width: 100%;
        height: 1;
        color: $warning;
    }
    RateVisitScreen #rating_display {
        text-align: center;
        width: 100%;
        height: 1;
        color: $error;
    }
    RateVisitScreen #submit {
        margin: 1 0;
        align-horizontal: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.rating = 0

    def compose(self):
        yield Header()
        yield Label("How was your visit?", id="rate_title")
        with Horizontal(id="stars_row"):
            for i in range(1, 6):
                yield Button("☆", id=f"star_{i}")
        yield Static("", id="rating_label")
        yield Static("", id="rating_display")
        yield Button("Update Rating", id="submit", variant="primary")
        yield Button("Delete Rating", id="delete", variant="default")
        yield Footer()

    def _refresh_stars(self):
        for i in range(1, 6):
            self.query_one(f"#star_{i}", Button).label = "★" if i <= self.rating else "☆"
        self.query_one("#rating_label", Static).update(RATING_LABELS.get(self.rating, ""))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("star_"):
            self.rating = int(event.button.id[-1])
            self._refresh_stars()
            self.query_one("#rating_display", Static).update("")
        elif event.button.id == "submit":
            if self.rating > 0:
                self.app.push_screen(MenuScreen())
            else:
                self.query_one("#rating_display", Static).update("Please select a rating first.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            self.rating = 0
            self._refresh_stars()
            self.query_one("#rating_display", Static).update("Rating deleted.")

class CustomCarStatusScreen(Screen):
    def __init__(self, cars: str):
        super().__init__()
        self.cars = [(car, i) for i, car in enumerate(cars)]
        self.status = [""]

    def compose(self) -> ComposeResult:
        yield Label("Custom Car Status")
        yield ListView(
            *[ListItem(Label(f"{car[0]} - Status: {self.status[car[1]]}")) for car in self.cars]
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

class AccountManagmentScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Account Management")
        yield Label("Here you can update your profile information and view your purchase history.")
        yield Label("Username: johndoe")
        yield Label("Email: example@gmail.com")
        yield Label("Phone: 555-1234")
        yield ListView(
            ListItem(Label("Update Profile")),
            ListItem(Label("Privacy Settings")),
            ListItem(Label("Delete All Cars")),
            ListItem(Label("Delete Account")),
        )
        yield Footer()
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render()
        if label == "Update Profile":
            self.app.push_screen(UpdateProfileScreen())
        if label == "Privacy Settings":
            self.app.push_screen(PrivacySettingsScreen())
        if label == "Delete Account":
            self.app.push_screen(DeleteAccountScreen())
        if label == "Delete All Cars":
            self.app.push_screen(DeleteCarsScreen())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class PrivacySettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Privacy Settings")
        yield Label("Do you want to REMOVE the date since youve own your cars?")
        yield ListView(
            ListItem(Label("Yes, remove the date")),
            ListItem(Label("No, keep the date")),
        )
        
        yield Footer()
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class DeleteAccountScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Delete Account")
        yield Label("Are you sure you want to delete your account? This action cannot be undone.")
        yield ListView(
            ListItem(Label("Yes, delete my account")),
            ListItem(Label("No, keep my account")),
        )
        
        yield Footer()
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class DeleteCarsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Delete All Cars")
        yield Label("Are you sure you want to delete all your cars? This action cannot be undone.")
        yield ListView(
            ListItem(Label("Yes, delete all my cars")),
            ListItem(Label("No, keep my cars")),
        )
        
        yield Footer()
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class UpdateProfileScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Update Profile")
        yield Label("Here you can update your profile information.")
        with Vertical():
            yield Label("Username:")
            yield Input(placeholder="Enter new username...", id="username")
            yield Label("Email:")
            yield Input(placeholder="Enter new email...", id="email")
            yield Label("Phone:")
            yield Input(placeholder="Enter new phone number...", id="phone")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result = self.query_one("#result", Label)
        if event.button.id == "submit":
            result.update(f"✓ Profile updated successfully!")
            time.sleep(2)  # Simulate processing time
            self.app.push_screen(AccountManagmentScreen())
        elif event.button.id == "clear":
            self.query_one("#username", Input).value = ""
            self.query_one("#email", Input).value = ""
            self.query_one("#phone", Input).value = ""

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

if __name__ == "__main__":
    MyApp().run()