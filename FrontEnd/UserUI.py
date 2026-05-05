import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
import random

# Allow running this file directly with `python FrontEnd/Base.py`
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Revisar.client_queries import (
    driver,
    get_customer_cars,
    get_customer_profile,
    update_customer_profile,
    get_customer_visits,
    add_visit_rating,
    get_rated_visits,
    remove_rating_from_visit,
    remove_since_from_all_cars,
    delete_customer_and_cars,
    remove_car_from_customer,
    remove_all_cars_from_customer,
    create_visit,
    add_costumer_cars_csv
)
from Revisar.dealershipAux import get_all_dealerships
from Revisar.buy_car import (
    get_showroom_cars,
    get_msrp,
    create_transaction_from_offers,
)

RATING_LABELS = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent"}


class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Welcome! Please enter your Customer ID to continue.")
        with Vertical():
            yield Label("Customer ID:")
            yield Input(placeholder="Enter your customer ID...", id="customer_id")
            yield Button("Login", id="login", variant="primary")
        yield Static("", id="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login":
            val = self.query_one("#customer_id", Input).value
            if val.isdigit():
                self.app.customer_id = int(val)
                self.app.switch_screen(MenuScreen())
            else:
                self.query_one("#error", Static).update("Please enter a valid numeric customer ID.")


class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Visit DealerShip")),
            ListItem(Label("Show My Cars")),
            ListItem(Label("Account")),
            ListItem(Label("Visit History")),
            ListItem(Label("Add Cars With CSV")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Quit":
            self.app.exit()
        elif label == "Visit DealerShip":
            self.app.push_screen(ShowDealershipsScreen())
        elif label == "Show My Cars":
            self.app.push_screen(ShowCarsScreen())
        elif label == "Account":
            self.app.push_screen(AccountManagmentScreen())
        elif label == "Visit History":
            self.app.push_screen(VisitHistoryScreen())
        elif label == "Add Cars With CSV":
            self.app.push_screen(AddCarsWithCSVScreen())


# ---------------------------------------------------------------------------
# Show My Cars  →  remove_car_from_customer
# ---------------------------------------------------------------------------

class ShowCarsScreen(Screen):
    def __init__(self):
        super().__init__()
        self.cars_data = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Your Cars  (select a car to remove it)")
        yield ListView(id="cars_list")
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

# if self.cars_data:
#                 for car in self.cars_data:
#                     year = car.get('year', '?')
#                     brand = car.get('brand', '?')
#                     model = car.get('model', '?')
#                     # If mileage is null/empty, show 0
#                     mileage = car.get('mileage')
#                     mileage_display = str(mileage) if mileage not in (None, "") else "0"
#                     # If since is null/empty, don't show it
#                     since = car.get('since')
#                     since_display = f" {since}" if since not in (None, "") else ""
#                     label = f"{year} {brand} {model} {mileage_display}{since_display} | Plate: {car.get('plate', 'N/A')}"
#                     lv.mount(ListItem(Label(label)))
#             else:
#                 self.query_one("#status", Static).update("No cars found.")
    def on_mount(self) -> None:
        try:
            self.cars_data = get_customer_cars(driver, self.app.customer_id)
            lv = self.query_one("#cars_list", ListView)
            if self.cars_data:
                for car in self.cars_data:
                    year = car.get('year', '?')
                    brand = car.get('brand', '?')
                    model = car.get('model', '?')
                    # If mileage is null/empty, show 0
                    mileage = car.get('mileage')
                    mileage_display = str(mileage) if mileage not in (None, "") else "0"
                    # If since is null/empty, don't show it
                    since = car.get('since')
                    since_display = f" | Since: {since}" if since not in (None, "") else ""
                    label = f"Year: {year} | Brand: {brand} | Model: {model} | Plate: {car.get('plate', 'N/A')} | Mileage: {mileage_display} {since_display} "
                    lv.mount(ListItem(Label(label)))
            else:
                self.query_one("#status", Static).update("No cars found.")
        except Exception as e:
            self.query_one("#status", Static).update(f"Error loading cars: {e}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if self.cars_data and idx is not None and 0 <= idx < len(self.cars_data):
            self.app.push_screen(RemoveCarScreen(self.cars_data[idx]))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class RemoveCarScreen(Screen):
    def __init__(self, car: dict):
        super().__init__()
        self.car = car

    def compose(self) -> ComposeResult:
        yield Header()
        year = self.car.get('year', '?')
        brand = self.car.get('brand', '?')
        model = self.car.get('model', '?')
        plate = self.car.get('plate', 'N/A')
        yield Label(f"Car: {year} {brand} {model}  |  Plate: {plate}")
        yield Label("Remove this car from your account?")
        yield ListView(
            ListItem(Label("Yes, remove this car")),
            ListItem(Label("No, keep this car")),
        )
        yield Static("", id="status")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Yes, remove this car":
            try:
                remove_car_from_customer(driver, self.app.customer_id, self.car["car_id"])
                self.app.pop_screen()
            except Exception as e:
                self.query_one("#status", Static).update(f"Error: {e}")
        elif label == "No, keep this car":
            self.app.pop_screen()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ---------------------------------------------------------------------------
# Visit DealerShip  →  get_showroom_cars  →  NegotiationScreen
#                   →  escape  →  RateVisitScreen  →  add_visit_rating
# ---------------------------------------------------------------------------

class ShowDealershipsScreen(Screen):
    def __init__(self):
        super().__init__()
        self.dealerships = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Select a Dealership to Visit")
        yield ListView(id="dealerships_list")
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            dealerships = get_all_dealerships(driver)
            self.dealerships = dealerships
            lv = self.query_one("#dealerships_list", ListView)
            if dealerships:
                for d in dealerships:
                    lv.mount(ListItem(Label(d.get("Name", "Unknown"))))
            else:
                self.query_one("#status", Static).update("No dealerships found.")
        except Exception as e:
            self.query_one("#status", Static).update(f"Error loading dealerships: {e}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.dealerships):
            dealership_id = self.dealerships[idx]["dealershipId"]
            self.app.push_screen(ShowRoomScreen(dealership_id=dealership_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class ShowRoomScreen(Screen):
    def __init__(self, dealership_id: int = 1):
        super().__init__()
        self.dealership_id = dealership_id
        self.cars_data = []
        self.apointment = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Welcome to the showroom!")
        yield ListView(id="cars_list")
        yield Static("", id="status")
        yield Label("\nPress Escape to rate your visit and go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.apointment = create_visit(driver, self.app.customer_id, self.dealership_id)
            self.cars_data = get_showroom_cars(driver, self.dealership_id)
            lv = self.query_one("#cars_list", ListView)
            if self.cars_data:
                for car in self.cars_data:
                    label = (
                        f"{car.get('year', '?')} {car.get('brand', '?')} {car.get('model', '?')}"
                        f" | ${car.get('msrp', 'N/A')} | {car.get('color', '')}"
                    )
                    lv.mount(ListItem(Label(label)))
            else:
                self.query_one("#status", Static).update("No cars available in this showroom.")
        except Exception as e:
            self.query_one("#status", Static).update(f"Error loading showroom: {e}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if self.cars_data and idx is not None and 0 <= idx < len(self.cars_data):
            car = {**self.cars_data[idx], "dealership_id": self.dealership_id}
            self.app.push_screen(NegotiationScreen(car, self.dealership_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.push_screen(RateVisitScreen(self.dealership_id))


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

    def __init__(self, dealership_id: int):
        super().__init__()
        self.rating = 0
        self.dealership_id = dealership_id


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
                try:
                    add_visit_rating(driver, self.app.customer_id, self.dealership_id, self.rating)
                    self.app.switch_screen(MenuScreen())
                except Exception as e:
                    self.query_one("#rating_display", Static).update(f"Error: {e}")
            else:
                self.query_one("#rating_display", Static).update("Please select a rating first.")


# ---------------------------------------------------------------------------
# Visit History  →  get_customer_visits / get_rated_visits
# PastRatingScreen  →  add_visit_rating / remove_rating_from_visit
# ---------------------------------------------------------------------------

class VisitHistoryScreen(Screen):
    def __init__(self):
        super().__init__()
        self.visits_data = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Visit History  (select a visit to rate or update its rating)")
        yield ListView(id="visits_list")
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.visits_data = get_customer_visits(driver, self.app.customer_id)
            lv = self.query_one("#visits_list", ListView)
            if self.visits_data:
                for v in self.visits_data:
                    name = v.get("d.Name", "?")
                    date = v.get("r.Date", "?")
                    lv.mount(ListItem(Label(f"{name} — {date}")))
            else:
                self.query_one("#status", Static).update("No visits found.")
        except Exception as e:
            self.query_one("#status", Static).update(f"Error: {e}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if not self.visits_data or idx is None or not (0 <= idx < len(self.visits_data)):
            return
        v = self.visits_data[idx]
        existing_rating = 0
        dealership_id = 0
        try:
            rated = get_rated_visits(driver, self.app.customer_id)
            for rv in rated.get("rated_visits", []):
                if rv["dealership"] == v.get("d.Name") and rv["date"] == v.get("r.Date"):
                    existing_rating = rv.get("rating", 0)
                    dealership_id = rv.get("dealership_id", 0)
                    break
        except Exception:
            pass
        self.app.push_screen(PastRatingScreen(
            customer_id=self.app.customer_id,
            dealership_id=dealership_id,
            dealership_name=v.get("d.Name", ""),
            date=v.get("r.Date", ""),
            existing_rating=existing_rating,
        ))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class PastRatingScreen(Screen):
    CSS = """
    PastRatingScreen Label#rate_title {
        text-align: center;
        width: 100%;
        padding: 1 0;
    }
    PastRatingScreen #stars_row {
        align: center middle;
        height: 10;
        padding: 1 0;
    }
    PastRatingScreen #stars_row Button {
        padding: 0 1;
        margin: 0 1;
        background: transparent;
        border: none;
        color: $warning;
    }
    PastRatingScreen #rating_label {
        text-align: center;
        width: 100%;
        height: 1;
        color: $warning;
    }
    PastRatingScreen #rating_display {
        text-align: center;
        width: 100%;
        height: 1;
        color: $error;
    }
    """

    def __init__(self, customer_id: int, dealership_id: int, dealership_name: str, date: str, existing_rating: int = 0):
        super().__init__()
        self.customer_id = customer_id
        self.dealership_id = dealership_id
        self.dealership_name = dealership_name
        self.date = date
        self.rating = existing_rating

    def compose(self):
        yield Header()
        yield Label(f"Visit: {self.dealership_name}  —  {self.date}", id="rate_title")
        with Horizontal(id="stars_row"):
            for i in range(1, 6):
                yield Button("☆", id=f"star_{i}")
        yield Static("", id="rating_label")
        yield Static("", id="rating_display")
        yield Button("Update Rating", id="submit", variant="primary")
        yield Button("Delete Rating", id="delete", variant="warning")
        yield Footer()

    def on_mount(self) -> None:
        if self.rating > 0:
            self._refresh_stars()

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
                try:
                    add_visit_rating(driver, self.customer_id, self.dealership_id, self.rating)
                    self.app.pop_screen()
                except Exception as e:
                    self.query_one("#rating_display", Static).update(f"Error: {e}")
            else:
                self.query_one("#rating_display", Static).update("Please select a rating first.")
        elif event.button.id == "delete":
            try:
                remove_rating_from_visit(driver, {
                    "customer_id": self.customer_id,
                    "dealership": self.dealership_name,
                    "date": self.date,
                })
                self.rating = 0
                self._refresh_stars()
                self.app.pop_screen()
            except Exception as e:
                self.query_one("#rating_display", Static).update(f"Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class AddCarsWithCSVScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Add Cars With CSV")
        yield Input(placeholder="Enter path to CSV file...", id="csv_path")
        yield Button("Submit", id="submit", variant="primary")
        yield Static("", id="result")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        csv_path = self.query_one("#csv_path", Input).value.strip()
        result = self.query_one("#result", Static)
        if event.button.id == "submit":
            if csv_path:
                try:
                    add_costumer_cars_csv(driver, self.app.customer_id, csv_path)
                    result.update("✓ Cars added successfully!")
                except Exception as e:
                    result.update(f"✗ Error: {e}")
            else:
                result.update("Please enter a valid CSV file path.")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ---------------------------------------------------------------------------
# Account  →  get_customer_profile / update_customer_profile /
#             remove_since_from_all_cars / remove_all_cars_from_customer /
#             delete_customer_and_cars
# ---------------------------------------------------------------------------

class AccountManagmentScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Account Management")
        yield Label("", id="name_label")
        yield Label("", id="email_label")
        yield Label("", id="phone_label")
        yield Static("", id="profile_error")
        yield ListView(
            ListItem(Label("Update Profile")),
            ListItem(Label("Privacy Settings")),
            ListItem(Label("Delete All Cars")),
            ListItem(Label("Delete Account")),
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            data = get_customer_profile(driver, self.app.customer_id)
            profile = data["profile"]
            self.query_one("#name_label", Label).update(f"Name:  {profile.get('Name', 'N/A')}")
            self.query_one("#email_label", Label).update(f"Email: {profile.get('Email', 'N/A')}")
            self.query_one("#phone_label", Label).update(f"Phone: {profile.get('Phone', 'N/A')}")
        except Exception as e:
            self.query_one("#profile_error", Static).update(f"Error loading profile: {e}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Update Profile":
            self.app.push_screen(UpdateProfileScreen())
        elif label == "Privacy Settings":
            self.app.push_screen(PrivacySettingsScreen())
        elif label == "Delete All Cars":
            self.app.push_screen(DeleteCarsScreen())
        elif label == "Delete Account":
            self.app.push_screen(DeleteAccountScreen())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class UpdateProfileScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Update Profile")
        yield Label("Leave a field empty to keep its current value.")
        with Vertical():
            yield Label("Name:")
            yield Input(placeholder="Enter new name...", id="username")
            yield Label("Email:")
            yield Input(placeholder="Enter new email...", id="email")
            yield Label("Phone:")
            yield Input(placeholder="Enter new phone number...", id="phone")
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
        yield Label("", id="result")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result = self.query_one("#result", Label)
        if event.button.id == "submit":
            updates = {}
            name = self.query_one("#username", Input).value.strip()
            email = self.query_one("#email", Input).value.strip()
            phone = self.query_one("#phone", Input).value.strip()
            if name:
                updates["Name"] = name
            if email:
                updates["Email"] = email
            if phone:
                updates["Phone"] = phone
            if updates:
                try:
                    update_customer_profile(driver, {"customer_id": self.app.customer_id}, updates)
                    result.update("✓ Profile updated successfully!")
                    self.app.pop_screen()
                except Exception as e:
                    result.update(f"Error: {e}")
            else:
                result.update("No changes entered.")
        elif event.button.id == "clear":
            self.query_one("#username", Input).value = ""
            self.query_one("#email", Input).value = ""
            self.query_one("#phone", Input).value = ""

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class PrivacySettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Privacy Settings")
        yield Label("Do you want to REMOVE the date since you've owned your cars?")
        yield ListView(
            ListItem(Label("Yes, remove the date")),
            ListItem(Label("No, keep the date")),
        )
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Yes, remove the date":
            try:
                result = remove_since_from_all_cars(driver, self.app.customer_id)
                self.query_one("#status", Static).update(
                    result.get("message", f"Updated {result.get('relationships_updated', 0)} car(s).")
                )
                self.app.pop_screen()
            except Exception as e:
                self.query_one("#status", Static).update(f"Error: {e}")
        elif label == "No, keep the date":
            self.app.pop_screen()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class DeleteCarsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Delete All Cars")
        yield Label("Are you sure you want to remove all your cars? This action cannot be undone.")
        yield ListView(
            ListItem(Label("Yes, delete all my cars")),
            ListItem(Label("No, keep my cars")),
        )
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Yes, delete all my cars":
            try:
                result = remove_all_cars_from_customer(driver, self.app.customer_id)
                self.query_one("#status", Static).update(
                    result.get("message", f"Removed {result.get('relationships_removed', 0)} car(s).")
                )
                self.app.pop_screen()
            except Exception as e:
                self.query_one("#status", Static).update(f"Error: {e}")
        elif label == "No, keep my cars":
            self.app.pop_screen()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class DeleteAccountScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Delete Account")
        yield Label("Are you sure you want to delete your account? This action cannot be undone.")
        yield ListView(
            ListItem(Label("Yes, delete my account")),
            ListItem(Label("No, keep my account")),
        )
        yield Static("", id="status")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.query_one(Label).render().plain
        if label == "Yes, delete my account":
            try:
                delete_customer_and_cars(driver, self.app.customer_id)
                self.app.exit()
            except Exception as e:
                self.query_one("#status", Static).update(f"Error: {e}")
        elif label == "No, keep my account":
            self.app.pop_screen()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ---------------------------------------------------------------------------
# Purchase vehicle workflow
# ShowRoomScreen → NegotiationScreen → TransactionScreen → PaymentScreen
#   get_showroom_cars / get_msrp / create_transaction_from_offers
# ---------------------------------------------------------------------------

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
    def __init__(self, car_data: dict, dealership_id: int):
        super().__init__()
        self.car_data = car_data
        self.dealership_id = dealership_id
        self.car_id = car_data.get("car_id")
        self.msrp = float(car_data.get("msrp") or 0)
        # Replicate negotiate_price acceptance range: 0–15 % around MSRP
        self.pct = random.uniform(0, 0.15)
        self.min_price = round(self.msrp * (1 - self.pct), 2)
        # offers[0] must be the MSRP (required by create_transaction_from_offers)
        self.offers = [self.msrp]

    def compose(self) -> ComposeResult:
        year = self.car_data.get("year", "")
        brand = self.car_data.get("brand", "")
        model = self.car_data.get("model", "")
        yield Header()
        yield Label(f"You selected: {year} {brand} {model}")
        yield Label(f"MSRP: ${self.msrp:,.2f}")
        with Vertical():
            yield Label("Your offer:")
            yield Input(placeholder="Enter your offer...", id="offer")
            yield Button("Submit offer", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
        yield Static("", id="result")
        yield Static("", id="offer_history")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        raw = self.query_one("#offer", Input).value.strip()
        result = self.query_one("#result", Static)
        offer_history = self.query_one("#offer_history", Static)

        if event.button.id == "submit":
            if not raw:
                result.update("✗ Please enter an offer")
                return
            try:
                offer = round(float(raw), 2)
            except ValueError:
                result.update("✗ Please enter a valid number")
                return

            self.offers.append(offer)
            history_lines = [f"${o:,.2f}" for o in self.offers[1:]]
            offer_history.update("Offers made:\n" + "\n".join(history_lines))

            if offer >= self.min_price:
                result.update(f"✓ Offer accepted: ${offer:,.2f}")
                self.app.push_screen(TransactionScreen(self.car_data, self.offers, self.dealership_id))
            else:
                result.update(f"✗ Offer rejected: ${offer:,.2f}  (minimum ~${self.min_price:,.2f})")
        elif event.button.id == "clear":
            self.query_one("#offer", Input).value = ""
            result.update("")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class TransactionScreen(Screen):
    def __init__(self, car_data: dict, offers: list, dealership_id: int = 1):
        super().__init__()
        self.car_data = car_data
        self.offers = offers
        self.dealership_id = dealership_id
        self.agreed_price = offers[-1]

    def compose(self) -> ComposeResult:
        year = self.car_data.get("year", "")
        brand = self.car_data.get("brand", "")
        model = self.car_data.get("model", "")
        yield Header()
        yield Label("Transaction Summary")
        yield Label(f"Car:    {year} {brand} {model}")
        yield Label(f"Price:  ${self.agreed_price:,.2f}")
        yield Label("\nSelect a payment method:")
        yield ListView(
            ListItem(Label("Credit Card")),
            ListItem(Label("Financing")),
            ListItem(Label("Bank Transfer")),
            ListItem(Label("Check")),
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_payment = event.item.query_one(Label).render().plain
        self.app.push_screen(PaymentScreen(selected_payment, self.car_data, self.offers, self.dealership_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class PaymentScreen(Screen):
    def __init__(self, selected_payment: str, car_data: dict, offers: list, dealership_id: int = 1):
        super().__init__()
        self.selected_payment = selected_payment
        self.car_data = car_data
        self.offers = offers
        self.agreed_price = offers[-1]
        self.dealership_id = dealership_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Payment — {self.selected_payment}  |  Total: ${self.agreed_price:,.2f}")
        if self.selected_payment == "Credit Card":
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
            with Vertical():
                yield Label("Months to Pay:")
                yield Input(placeholder="Enter the number of months...", id="months")
                yield Button("Check Monthly Payments", id="checkmp", variant="warning")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        elif self.selected_payment == "Bank Transfer":
            with Vertical():
                yield Label("Bank Name:")
                yield Input(placeholder="Enter your bank name...", id="bank_name")
                yield Label("Account Number:")
                yield Input(placeholder="Enter your account number...", id="account_number")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        elif self.selected_payment == "Check":
            with Vertical():
                yield Label("Check Number:")
                yield Input(placeholder="Enter your check number...", id="check_number")
                yield Label("Bank Name:")
                yield Input(placeholder="Enter your bank name...", id="bank_name_check")
                yield Button("Submit", id="submit", variant="primary")
                yield Button("Clear", id="clear", variant="default")
        yield Static("", id="result")
        yield Static("", id="financing_result")
        yield Label("\nPress Escape to go back")
        yield Footer()

    def _get_financing_months(self) -> int | None:
        if self.selected_payment != "Financing":
            return None
        try:
            val = self.query_one("#months", Input).value.strip()
            return int(val) if val else None
        except (ValueError, Exception):
            return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        result = self.query_one("#result", Static)

        if event.button.id == "submit":
            try:
                financing_months = self._get_financing_months()
                create_transaction_from_offers(
                    driver,
                    success=True,
                    offers=list(self.offers),
                    car_id=self.car_data["car_id"],
                    customer_id=self.app.customer_id,
                    payment_type=self.selected_payment,
                    financing_months=financing_months,
                    dealership_id=self.dealership_id
                )
                result.update("✓ Purchase complete! Transaction saved.")
                self.app.push_screen(RateVisitScreen(dealership_id=self.dealership_id))
            except Exception as e:
                result.update(f"✗ Transaction failed: {e}")

        elif event.button.id == "clear":
            result.update("")

        elif event.button.id == "checkmp":
            months = self.query_one("#months", Input).value.strip()
            if months and months.isdigit():
                monthly = self.agreed_price / int(months)
                self.query_one("#financing_result", Static).update(
                    f"{months} months at ${monthly:,.2f} / month"
                )

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ---------------------------------------------------------------------------

