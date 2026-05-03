import psutil  # pip install psutil
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Horizontal, Vertical

class Dashboard(App):
    CSS = """
    Horizontal { height: auto; }
    Static { border: round white; padding: 0 1; width: 1fr; }
    DataTable { height: 10; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                yield Static("", id="cpu")
                yield Static("", id="mem")
                yield Static("", id="disk")
            yield DataTable(id="processes")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#processes", DataTable)
        table.add_columns("PID", "Name", "CPU %", "Mem %")
        self.update_stats()
        self.set_interval(2, self.update_stats)  # refresh every 2 seconds

    def update_stats(self) -> None:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        self.query_one("#cpu").update(f"CPU\n{self._bar(cpu)} {cpu:.0f}%")
        self.query_one("#mem").update(f"Memory\n{self._bar(mem)} {mem:.0f}%")
        self.query_one("#disk").update(f"Disk\n{self._bar(disk)} {disk:.0f}%")

        table = self.query_one("#processes", DataTable)
        table.clear()
        for proc in sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
                           key=lambda p: p.info["cpu_percent"] or 0, reverse=True)[:5]:
            i = proc.info
            table.add_row(str(i["pid"]), i["name"][:20], f"{i['cpu_percent']:.1f}", f"{i['memory_percent']:.1f}")

    def _bar(self, pct: float, width: int = 10) -> str:
        filled = int(pct / 100 * width)
        return "█" * filled + "░" * (width - filled)

if __name__ == "__main__":
    Dashboard().run()