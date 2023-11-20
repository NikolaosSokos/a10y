from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Select, Input, Checkbox, Header
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem


# PENDINGS:
#  - how to lose focus from all elements


class Requests(Static):
    """Web service request control widget"""

    def compose(self) -> ComposeResult:
        yield Static("Requests control", id="request-title")
        yield Container(
            Horizontal(
                Label("Node:", classes="request-label", id="node-label"),
                Select([
                    ("NOA", "https://eida.gein.noa.gr/fdsnws/availability/1/query"),
                    ("RESIF", "I don't know the URL")
                    ], prompt="Choose Node")
                ),
            Input(placeholder="Enter BaseURL", id="baseurl"), # for the case of user entering availability endpoint URL
            id="request-node"
        )
        yield Horizontal(
            Label("Network:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input"),
                Dropdown(items=[DropdownItem("Glasgow"), DropdownItem("Edinburgh"), DropdownItem("Aberdeen"), DropdownItem("Dundee")])
            ),
            Label("Station:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input"),
                Dropdown(items=[DropdownItem("Glasgow"), DropdownItem("Edinburgh"), DropdownItem("Aberdeen"), DropdownItem("Dundee")])
            ),
            Label("Location:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input"),
                Dropdown(items=[DropdownItem("Glasgow"), DropdownItem("Edinburgh"), DropdownItem("Aberdeen"), DropdownItem("Dundee")])
            ),
            Label("Channel:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input"),
                Dropdown(items=[DropdownItem("Glasgow"), DropdownItem("Edinburgh"), DropdownItem("Aberdeen"), DropdownItem("Dundee")])
            ),
            id="nslc"
        )
        yield Horizontal(
            Label("Start Time:", classes="request-label"),
            Input(classes="date-input"),
            Label("End Time:", classes="request-label"),
            Input(classes="date-input"),
            id="timeframe"
        )
        yield Horizontal(
            Label("Merge Options:", classes="request-label"),
            Checkbox("Samplerate"),
            Checkbox("Quality"),
            Checkbox("Overlap"),
            id="merge"
        )
        yield Horizontal(
            Label("Quality:", classes="request-label"),
            Checkbox("D", True),
            Checkbox("M", True),
            id="quality"
        )


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield Static("Status")
        yield Static("", id="status-line")


class AvailabilityUI(App):
    CSS_PATH = "availability_ui.css"
    BINDINGS = [("escape", "unfocus_input", "Lose input focus")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Static("Explanations", classes="box"),
            Requests(classes="box"),
            Status(classes="box", id="status-widget"),
            Static("Results", classes="box")
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """A function to change status when a Node is selected"""
        # for the case of user typing availability endpoint URL
        if event.value:
            self.query_one("#baseurl").add_class("hide")
        else:
            self.query_one("#baseurl").remove_class("hide")

        self.query_one("#status-line").update(event.value if event.value else "")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """A function to change status when an availability endpoint URL is submitted (i.e. is typed and enter is hit)"""
        if event.input == self.query_one("#baseurl"):
            self.query_one("#status-line").update(event.value)

    def action_unfocus_input(self) -> None:
        """An action to lose focus from input"""
        for item in self.query():
            item.blur()


if __name__ == "__main__":
    app = AvailabilityUI()
    app.run()
