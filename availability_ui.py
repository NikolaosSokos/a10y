from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Static, Select, Input, Header


# PENDINGS:
#  - how to lose focus from Input
#  - print in the status either Input or selected url (look on_input_submitted for this)
#  - button to end up writing Input and issue request (look Input.Submitted for this)


class Requests(Static):
    """Web service request control widget"""

    def compose(self) -> ComposeResult:
        yield Static("Requests control")
        yield Select([("NOA", "https://eida.gein.noa.gr/fdsnws/availability/1/query"), ("RESIF", "I don't know the URL")])
        yield Input(placeholder="Enter BaseURL") # for the case of user entering availability endpoint


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield Static("Status")
        yield Static("", id="status-line")


class AvailabilityUI(App):
    CSS_PATH = "availability_ui.tcss"
    BINDINGS = [("escape", "unfocus_input", "Lose input focus")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Explanations", classes="box")
        yield Requests(classes="box")
        yield Status(classes="box", id="status-widget")
        yield Static("Results", classes="box")

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        # for the case of user entering availability endpoint
        if event.value:
            self.query_one("Input").add_class("hide")
        else:
            self.query_one("Input").remove_class("hide")

        self.query_one("#status-line").update(event.value if event.value else "")

    def action_unfocus_input(self) -> None:
        """An action to lose focus from input"""
        for item in self.query():
            item.blur()


if __name__ == "__main__":
    app = AvailabilityUI()
    app.run()
