import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Input, Static
from textual.screen import Screen
from textual.containers import Vertical, Horizontal

from Revisar.dealershipTasks import (
    create_backorder, get_dealership_visits, get_showroom_avg_msrp,
    get_monthly_sales_report, set_discount_old_cars, adjust_showroom_msrp,
    adjust_showroom_msrp_by_brand, remove_discount_by_brand, set_tracking,
    get_cars_on_shipment, get_all_backorders, delete_showroom_car, toggle_test_drive
)
from Revisar.dealershipAux import get_all_manufacturers, driver
from Revisar.buy_car import get_showroom_cars

brand_models = {
    "Toyota":  ["Corolla", "Camry", "RAV4", "Hilux"],
    "Ford":    ["F150", "Mustang", "Explorer"],
    "BMW":     ["320i", "X5", "M3"],
    "Tesla":   ["Model3", "ModelX", "Cybertruck"],
    "Hyundai": ["Elantra", "Tucson", "SantaFe"],
}

COLORS     = ["White", "Black", "Red", "Blue", "Silver", "Gray"]
FUEL_TYPES = ["Electric", "Diesel", "Gas"]


# ─── MENU ────────────────────────────────────────────────────────────────────

class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Inventory")),
            ListItem(Label("Track Shipments")),
            ListItem(Label("Discount Management")),
            ListItem(Label("Back Order")),
            ListItem(Label("Transaction Reports")),
            ListItem(Label("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = str(event.item.query_one(Label).render())
        if label == "Quit":
            self.app.exit()
        elif label == "Inventory":
            self.app.push_screen(InventoryScreen())
        elif label == "Track Shipments":
            self.app.push_screen(TrackShipmentsScreen())
        elif label == "Discount Management":
            self.app.push_screen(DiscountManagementScreen())
        elif label == "Back Order":
            self.app.push_screen(BackOrderScreen())
        elif label == "Transaction Reports":
            self.app.push_screen(TransactionReportsScreen())


# ─── INVENTORY ───────────────────────────────────────────────────────────────

class InventoryScreen(Screen):
    CSS = """
    InventoryScreen { overflow-y: auto; }
    InventoryScreen #stats { padding: 1 2; }
    InventoryScreen #car_list { height: 10; }
    InventoryScreen .section-label { text-style: bold; padding: 1 0 0 0; }
    InventoryScreen .input-row { height: auto; padding: 0 0 1 0; }
    InventoryScreen .input-row Button { margin: 0 0 0 1; }
    InventoryScreen #result { padding: 1 0; }
    """

    def __init__(self):
        super().__init__()
        self.cars_data: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            # yield Static("Loading stats…", id="stats")
            yield Label("Showroom Cars", classes="section-label")
            yield ListView(id="car_list")
            # yield Label("Adjust MSRP (enter % then press button)", classes="section-label")
            # with Horizontal(classes="input-row"):
            #     yield Input(placeholder="e.g. 5 for +5%, -5 for -5%", id="adj_pct")
            #     yield Button("Adjust All", id="adjust_all", variant="primary")
            # with Horizontal(classes="input-row"):
            #     yield Input(placeholder="Brand name", id="adj_brand")
            #     yield Button("Adjust by Brand", id="adjust_brand", variant="default")
            yield Static("", id="result")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        did = self.app.dealership_id
        # try:
        #     stats = get_showroom_avg_msrp(driver, did)
        #     self.query_one("#stats", Static).update(
        #         f"Total: {stats['total_cars']} cars  |  "
        #         f"Avg MSRP: ${stats['avg_msrp'] or 0:,.0f}  |  "
        #         f"Min: ${stats['min_msrp'] or 0:,.0f}  |  Max: ${stats['max_msrp'] or 0:,.0f}"
        #     )
        # except Exception as e:
        #     self.query_one("#stats", Static).update(f"Stats unavailable: {e}")

        lv = self.query_one("#car_list", ListView)
        try:
            self.cars_data = get_showroom_cars(driver, self.app.dealership_id)
            for car in self.cars_data:
                msrp = car.get("msrp") or 0
                lv.mount(ListItem(
                    Label(f"{car.get('year','')} {car.get('brand','')} {car.get('model','')} — ${msrp:,.0f}"),
                    id=f"car_{car['car_id']}",
                ))
            if not self.cars_data:
                lv.mount(ListItem(Label("No cars in showroom")))
        except Exception as e:
            lv.mount(ListItem(Label(f"Error loading cars: {e}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("car_"):
            car_id = item_id[len("car_"):]
            car = next((c for c in self.cars_data if str(c["car_id"]) == car_id), None)
            if car:
                self.app.push_screen(CarManagementScreen(car))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        result = self.query_one("#result", Static)
        did = self.app.dealership_id
        pct_str = self.query_one("#adj_pct", Input).value.strip()
        try:
            pct = float(pct_str) / 100 if pct_str else None
        except ValueError:
            result.update("✗ Invalid adjustment percentage")
            return

        if bid == "adjust_all":
            if pct is None:
                result.update("✗ Enter adjustment percentage")
                return
            try:
                res = adjust_showroom_msrp(driver, did, pct)
                result.update(f"✓ Updated {res['updated_cars']} cars")
            except Exception as e:
                result.update(f"✗ Error: {e}")

        elif bid == "adjust_brand":
            brand = self.query_one("#adj_brand", Input).value.strip()
            if not brand:
                result.update("✗ Enter brand name")
                return
            if pct is None:
                result.update("✗ Enter adjustment percentage")
                return
            try:
                res = adjust_showroom_msrp_by_brand(driver, did, brand, pct)
                result.update(f"✓ Updated {res['updated_cars']} {brand} cars")
            except Exception as e:
                result.update(f"✗ Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class CarManagementScreen(Screen):
    def __init__(self, car: dict):
        super().__init__()
        self.car = car

    def compose(self) -> ComposeResult:
        c = self.car
        msrp = c.get("msrp") or 0
        yield Header()
        with Vertical():
            yield Static(
                f"Brand:   {c.get('brand','')}\n"
                f"Model:   {c.get('model','')}\n"
                f"Year:    {c.get('year','')}\n"
                f"Color:   {c.get('color','')}\n"
                f"Plate:   {c.get('plate','')}\n"
                f"MSRP:    ${msrp:,.0f}\n"
                f"On Site: {c.get('on_site_since','')}\n"
                f"Negotiable: {c.get('negotiable','')}"
            )
            yield Button("Delete Car from Showroom", id="delete", variant="error")
            yield Static("", id="result")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            result = self.query_one("#result", Static)
            try:
                delete_showroom_car(driver, self.app.dealership_id, str(self.car["car_id"]))
                result.update("✓ Car deleted from showroom")
                event.button.disabled = True
            except Exception as e:
                result.update(f"✗ Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ─── TRACK SHIPMENTS ─────────────────────────────────────────────────────────

class TrackShipmentsScreen(Screen):
    CSS = """
    TrackShipmentsScreen { overflow-y: auto; }
    TrackShipmentsScreen #ship_list { height: 12; }
    TrackShipmentsScreen #result { padding: 1 0; }
    """

    def __init__(self):
        super().__init__()
        self.shipments_data: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Shipments in Transit")
            yield ListView(id="ship_list")
            yield Button("Mark Untracked as PENDING", id="mark_pending", variant="primary")
            yield Static("", id="result")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        did = self.app.dealership_id
        lv = self.query_one("#ship_list", ListView)
        try:
            self.shipments_data = get_cars_on_shipment(driver, did)
            for ship in self.shipments_data:
                tracking = ship.get("tracking_status") or "—"
                lv.mount(ListItem(Label(
                    f"{ship.get('brand','')} {ship.get('model','')} {ship.get('year','')}  [{tracking}]"
                )))
            if not self.shipments_data:
                lv.mount(ListItem(Label("No active shipments")))
        except Exception as e:
            lv.mount(ListItem(Label(f"Error: {e}")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "mark_pending":
            result = self.query_one("#result", Static)
            try:
                res = set_tracking(driver, self.app.dealership_id, "PENDING")
                result.update(f"✓ Marked {res['updated_shipments']} shipments as PENDING")
            except Exception as e:
                result.update(f"✗ Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ─── DISCOUNT MANAGEMENT ─────────────────────────────────────────────────────

class DiscountManagementScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Set Discount on Old Cars")),
            ListItem(Label("Remove Discount by Brand")),
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = str(event.item.query_one(Label).render())
        if label == "Set Discount on Old Cars":
            self.app.push_screen(SetOldCarsDiscountScreen())
        elif label == "Remove Discount by Brand":
            self.app.push_screen(RemoveDiscountScreen())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class SetOldCarsDiscountScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Set Discount on Old Cars (cars from previous years)")
            yield Label("Discount Percentage:")
            yield Input(placeholder="e.g. 10 for 10%", id="discount")
            yield Button("Apply Discount", id="submit", variant="primary")
            yield Button("Clear", id="clear", variant="default")
            yield Static("", id="result")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        result = self.query_one("#result", Static)
        if bid == "submit":
            pct_str = self.query_one("#discount", Input).value.strip()
            try:
                pct = float(pct_str) / 100
            except ValueError:
                result.update("✗ Invalid percentage")
                return
            try:
                res = set_discount_old_cars(driver, self.app.dealership_id, pct)
                result.update(f"✓ Discount applied to {res['updated_cars']} cars")
            except Exception as e:
                result.update(f"✗ Error: {e}")
        elif bid == "clear":
            self.query_one("#discount", Input).value = ""
            result.update("")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class RemoveDiscountScreen(Screen):
    CSS = """
    RemoveDiscountScreen .btn-row { height: auto; padding: 0 0 1 0; }
    RemoveDiscountScreen .btn-row Button { margin: 0 1 0 0; }
    """

    def __init__(self):
        super().__init__()
        self.sel_brand: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Remove Discount by Brand")
            yield Label("Select Brand:")
            with Horizontal(id="brand_row", classes="btn-row"):
                for b in brand_models:
                    yield Button(b, id=f"brand_{b}")
            yield Button("Remove Discount", id="submit", variant="error")
            yield Static("", id="result")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("brand_"):
            self.sel_brand = bid[len("brand_"):]
            for btn in self.query_one("#brand_row", Horizontal).query(Button):
                btn.variant = "primary" if btn.id == bid else "default"
        elif bid == "submit":
            result = self.query_one("#result", Static)
            if not self.sel_brand:
                result.update("✗ Select a brand first")
                return
            try:
                res = remove_discount_by_brand(driver, self.app.dealership_id, self.sel_brand)
                result.update(f"✓ Removed discount from {res['updated_cars']} {self.sel_brand} cars")
            except Exception as e:
                result.update(f"✗ Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ─── BACK ORDER ──────────────────────────────────────────────────────────────

class BackOrderScreen(Screen):
    CSS = """
    BackOrderScreen { overflow-y: auto; }
    BackOrderScreen #form { padding: 1 2; height: auto; }
    BackOrderScreen .section-label { text-style: bold; padding: 1 0 0 0; }
    BackOrderScreen .btn-row { height: auto; padding: 0 0 1 0; }
    BackOrderScreen .btn-row Button { margin: 0 1 0 0; }
    BackOrderScreen #action-row { height: auto; padding: 1 0 0 0; }
    BackOrderScreen #result { padding: 1 0; }
    """

    def __init__(self):
        super().__init__()
        self.sel_brand:           str | None = None
        self.sel_model:           str | None = None
        self.sel_color:           str | None = None
        self.sel_fuel:            str | None = None
        self.sel_manufacturer_id: str | None = None
        self.manufacturers: list = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="form"):
            yield Label("Manufacturer", classes="section-label")
            with Horizontal(id="mfr_row", classes="btn-row"):
                yield Label("Loading manufacturers…", id="mfr_loading")

            yield Label("Brand", classes="section-label")
            with Horizontal(id="brand_row", classes="btn-row"):
                for b in brand_models:
                    yield Button(b, id=f"brand_{b}")

            yield Label("Model  ← select a brand first", id="model_label", classes="section-label")
            with Horizontal(id="model_row", classes="btn-row"):
                pass

            yield Label("Color", classes="section-label")
            with Horizontal(id="color_row", classes="btn-row"):
                for c in COLORS:
                    yield Button(c, id=f"color_{c}")

            yield Label("Fuel Type", classes="section-label")
            with Horizontal(id="fuel_row", classes="btn-row"):
                for f in FUEL_TYPES:
                    yield Button(f, id=f"fuel_{f}")

            yield Label("Destination Country", classes="section-label")
            yield Input(placeholder="e.g. Guatemala", id="destination_country")

            with Horizontal(id="action-row"):
                yield Button("Submit",         id="submit",         variant="primary")
                yield Button("Clear",          id="clear",          variant="default")
                yield Button("View Backorders", id="view_backorders", variant="default")

            yield Static("", id="result")

        yield Label("Press Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.manufacturers = get_all_manufacturers(driver)
            mfr_row = self.query_one("#mfr_row", Horizontal)
            self.query_one("#mfr_loading", Label).remove()
            for m in self.manufacturers:
                label = f"{m['Brand']} – {m['Group']}"
                mfr_row.mount(Button(label, id=f"mfr_{m['manufacturerId']}"))
        except Exception as e:
            self.query_one("#mfr_loading", Label).update(f"Error loading manufacturers: {e}")

    def _highlight(self, group_id: str, prefix: str, value: str) -> None:
        for btn in self.query_one(f"#{group_id}", Horizontal).query(Button):
            btn.variant = "primary" if btn.id == f"{prefix}_{value}" else "default"

    def _update_models(self) -> None:
        self.sel_model = None
        row = self.query_one("#model_row", Horizontal)
        for btn in list(row.query(Button)):
            btn.remove()
        if self.sel_brand:
            for m in brand_models[self.sel_brand]:
                row.mount(Button(m, id=f"model_{m}"))
            self.query_one("#model_label", Label).update("Model")
        else:
            self.query_one("#model_label", Label).update("Model  ← select a brand first")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid.startswith("mfr_"):
            self.sel_manufacturer_id = bid[len("mfr_"):]
            for btn in self.query_one("#mfr_row", Horizontal).query(Button):
                btn.variant = "primary" if btn.id == bid else "default"

        elif bid.startswith("brand_"):
            self.sel_brand = bid[len("brand_"):]
            self._highlight("brand_row", "brand", self.sel_brand)
            self._update_models()

        elif bid.startswith("model_"):
            self.sel_model = bid[len("model_"):]
            self._highlight("model_row", "model", self.sel_model)

        elif bid.startswith("color_"):
            self.sel_color = bid[len("color_"):]
            self._highlight("color_row", "color", self.sel_color)

        elif bid.startswith("fuel_"):
            self.sel_fuel = bid[len("fuel_"):]
            self._highlight("fuel_row", "fuel", self.sel_fuel)

        elif bid == "submit":
            self._submit()
        elif bid == "clear":
            self._clear()
        elif bid == "view_backorders":
            self.app.push_screen(ViewBackordersScreen())

    def _submit(self) -> None:
        result = self.query_one("#result", Static)
        country = self.query_one("#destination_country", Input).value.strip()
        missing = [
            name for name, val in [
                ("Manufacturer",        self.sel_manufacturer_id),
                ("Brand",               self.sel_brand),
                ("Model",               self.sel_model),
                ("Color",               self.sel_color),
                ("Fuel Type",           self.sel_fuel),
                ("Destination Country", country or None),
            ]
            if not val
        ]
        if missing:
            result.update(f"✗ Missing: {', '.join(missing)}")
            return
        try:
            create_backorder(
                driver,
                manufacturer_id=self.sel_manufacturer_id,
                fuel_type=self.sel_fuel,
                model=self.sel_model,
                brand=self.sel_brand,
                color=self.sel_color,
                destination_country=country,
            )
            result.update(
                f"✓ Back order submitted!\n"
                f"  {self.sel_brand} {self.sel_model}  ·  {self.sel_color}  ·  {self.sel_fuel}\n"
                f"  Destination: {country}"
            )
        except Exception as e:
            result.update(f"✗ Error: {e}")

    def _clear(self) -> None:
        for group_id in ("mfr_row", "brand_row", "color_row", "fuel_row"):
            try:
                for btn in self.query_one(f"#{group_id}", Horizontal).query(Button):
                    btn.variant = "default"
            except Exception:
                pass
        for btn in list(self.query_one("#model_row", Horizontal).query(Button)):
            btn.remove()
        self.query_one("#destination_country", Input).value = ""
        self.query_one("#result", Static).update("")
        self.query_one("#model_label", Label).update("Model  ← select a brand first")
        self.sel_brand = self.sel_model = self.sel_color = self.sel_fuel = self.sel_manufacturer_id = None

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class ViewBackordersScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Loading…", id="content")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            orders = get_all_backorders(driver, self.app.dealership_id)
            if not orders:
                self.query_one("#content", Static).update("No backorders found.")
                return
            lines = [
                f"{o.get('brand','')} {o.get('model','')} — {o.get('color','')} — ID: {o.get('car_id','')}"
                for o in orders
            ]
            self.query_one("#content", Static).update("\n".join(lines))
        except Exception as e:
            self.query_one("#content", Static).update(f"Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ─── TRANSACTION REPORTS ─────────────────────────────────────────────────────

class TransactionReportsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            ListItem(Label("Sales by Month"),          id="report_1"),
            ListItem(Label("Dealership Visits"),       id="report_2"),
            ListItem(Label("Average Showroom Price"),  id="report_3"),
        )
        yield Label("\nPress Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        rowId = event.item.id or ""
        if rowId == "report_1":
            self.app.push_screen(SalesReportScreen())
        elif rowId == "report_2":
            self.app.push_screen(VisitsReportScreen())
        elif rowId == "report_3":
            self.app.push_screen(AveragePriceReportScreen())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class SalesReportScreen(Screen):
    CSS = """
    SalesReportScreen #sales_list { height: 12; }
    SalesReportScreen .input-row { height: auto; }
    """

    def __init__(self):
        super().__init__()
        self.results: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Sales by Month")
            with Vertical():
                yield Input(placeholder="Month (1-12)", id="month_input")
                yield Button("Load", id="load", variant="primary")
            yield ListView(id="sales_list")
            yield Static("", id="status")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "load":
            return
        status = self.query_one("#status", Static)
        month_str = self.query_one("#month_input", Input).value.strip()
        try:
            month = int(month_str)
            if not 1 <= month <= 12:
                raise ValueError
        except ValueError:
            status.update("✗ Enter a valid month (1-12)")
            return
        try:
            self.results = get_monthly_sales_report(driver, self.app.dealership_id, month)
            lv = self.query_one("#sales_list", ListView)
            for item in list(lv.query(ListItem)):
                item.remove()
            if not self.results:
                lv.mount(ListItem(Label("No sales found for this month")))
            else:
                for r in self.results:
                    lv.mount(ListItem(Label(
                        f"{r.get('customer_name','')}  |  ${r.get('sale_amount', 0)}  |  {r.get('sale_date','')}"
                    )))
            status.update(f"✓ {len(self.results)} records")
        except Exception as e:
            status.update(f"✗ Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class VisitsReportScreen(Screen):
    CSS = """
    VisitsReportScreen #visit_list { height: 14; }
    """

    def __init__(self):
        super().__init__()
        self.visits_data: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Dealership Visits — Last 30 Days")
            yield ListView(id="visit_list")
            yield Static("", id="status")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if not (0 <= idx < len(self.visits_data)):
            return
        visit = self.visits_data[idx]
        try:
            res = toggle_test_drive(
                driver,
                str(self.app.dealership_id),
                str(visit["customer_id"]),
                str(visit["visit_date"])[:10],
            )
            visit["test_drive"] = res["new_test_drive_value"]
            td = "✓ Test Drive" if visit["test_drive"] else "✗ Test Drive"
            event.item.query_one(Label).update(
                f"{visit.get('customer_name','')}  |  {visit.get('visit_date','')}  |  {td}"
            )
        except Exception as e:
            self.query_one("#status", Static).update(f"Error: {e}")

    def on_mount(self) -> None:
        lv = self.query_one("#visit_list", ListView)
        try:
            self.visits_data = get_dealership_visits(driver, self.app.dealership_id)
            for v in self.visits_data:
                td = "✓ Test Drive" if v.get("test_drive") else "✗ Test Drive"
                lv.mount(ListItem(Label(
                    f"{v.get('customer_name','')}  |  {v.get('visit_date','')}  |  {td}"
                )))
            if not self.visits_data:
                lv.mount(ListItem(Label("No visits in the last month")))
            self.query_one("#status", Static).update(f"{len(self.visits_data)} visits found")
        except Exception as e:
            lv.mount(ListItem(Label(f"Error: {e}")))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class AveragePriceReportScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Loading…", id="content")
        yield Label("Press Escape to go back")
        yield Footer()

    def on_mount(self) -> None:
        try:
            stats = get_showroom_avg_msrp(driver, self.app.dealership_id)
            self.query_one("#content", Static).update(
                f"Showroom MSRP Statistics\n\n"
                f"  Total Cars:  {stats['total_cars']}\n"
                f"  Average:     ${stats['avg_msrp'] or 0:,.2f}\n"
                f"  Minimum:     ${stats['min_msrp'] or 0:,.2f}\n"
                f"  Maximum:     ${stats['max_msrp'] or 0:,.2f}"
            )
        except Exception as e:
            self.query_one("#content", Static).update(f"Error: {e}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


# ─── APP ─────────────────────────────────────────────────────────────────────

class MyApp(App):
    def on_mount(self) -> None:
        self.dealership_id: int = 0
        self.push_screen(MenuScreen())


if __name__ == "__main__":
    MyApp().run()
