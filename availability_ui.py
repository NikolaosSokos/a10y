from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Select, Input, Checkbox, Button, Header
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem
import requests


# PENDINGS:
#  - how to lose focus from all elements
#  - typing URL handling
#  - date and relative date selection that will add things in the start time and end time when something is chosen
#  - send button handling

class Requests(Static):
    """Web service request control widget"""

    def compose(self) -> ComposeResult:
        yield Static("Requests control", id="request-title")
        yield Container(
            Horizontal(
                Label("Node:", classes="request-label", id="node-label"),
                Select([
                    ("NOA", "https://eida.gein.noa.gr/fdsnws/"),
                    ("RESIF", "I don't know the URL")
                    ], prompt="Choose Node", id="nodes")
                ),
            Input(placeholder="Type Node Availability URL", id="baseurl"), # for the case of user entering availability endpoint URL
            Button("Send", variant="primary", id="request-button"),
            id="request-node"
        )
        yield Horizontal(
            Label("Network:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input", id="network"),
                Dropdown(items=[], id="networks")
            ),
            Label("Station:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input", id="station"),
                Dropdown(items=[], id="stations")
            ),
            Label("Location:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input", id="location"),
                Dropdown(items=[], id="locations")
            ),
            Label("Channel:", classes="request-label"),
            AutoComplete(
                Input(classes="short-input", id="channel"),
                Dropdown(items=[], id="channels")
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
        """A function to issue appropriate request and update status when a Node is selected"""
        # for the case of user typing availability endpoint URL
        if event.value:
            self.query_one("#baseurl").add_class("hide")
        else:
            self.query_one("#baseurl").remove_class("hide")

        if event.value:
            self.query_one("#status-line").update(f"Checking {event.value}availability/1/query")
            r = requests.get(event.value+"availability/1/query")
            if 'availability' in r.text:
                # get available networks from FDSN
                self.query_one("#status-line").update(f'Retrieving Networks from {event.value}station/1/query?level=network&format=text')
                r = requests.get(event.value+"station/1/query?level=network&format=text")
                if r.status_code != 200:
                    self.query_one("#status-line").update(f"[red]Couldn't retrieve Networks from {event.value}station/1/query?level=network&format=text[/red]")
                autocomplete_nets = self.query_one("#networks")
                autocomplete_nets.items = [DropdownItem(n.split('|')[0]) for n in r.text.splitlines()[1:]]
            else:
                self.query_one("#status-line").update('[red]Availability URL is not valid[/red]')
        else:
            self.query_one("#status-line").update("")


    def on_input_submitted(self, event: Input.Submitted) -> None:
        """A function to change status when an availability endpoint URL is submitted (i.e. is typed and enter is hit)"""
        if event.input == self.query_one("#baseurl"):
            self.query_one("#status-line").update(event.value)
        elif event.input == self.query_one("#network"):
            # handle case of submitting without having selected Node
            if self.query_one('#nodes').value is None:
                self.query_one("#status-line").update(f"[red]Please select a Node[/red]")
                return None
            # get available stations from FDSN
            net = self.query_one('#network').value
            self.query_one("#status-line").update(f"Retrieving Stations from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}&format=text")
            r = requests.get(f"{self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}&format=text")
            if r.status_code != 200:
                self.query_one("#status-line").update(f"[red]Couldn't retrieve Stations from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}&format=text[/red]")
            else:
                autocomplete = self.query_one("#stations")
                autocomplete.items = [DropdownItem(s.split('|')[1]) for s in r.text.splitlines()[1:]]
        elif event.input == self.query_one("#station"):
            # handle case of submitting without having selected Node
            if self.query_one('#nodes').value is None:
                self.query_one("#status-line").update(f"[red]Please select a Node[/red]")
                return None
            # get available channels from FDSN
            net = self.query_one('#network').value
            sta = self.query_one('#station').value
            self.query_one("#status-line").update(f"Retrieving Channels from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}{'&station='+sta if sta else ''}&level=channel&format=text")
            r = requests.get(f"{self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}{'&station='+sta if sta else ''}&level=channel&format=text")
            if r.status_code != 200:
                self.query_one("#status-line").update(f"[red]Couldn't retrieve Channels from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}{'&station='+sta if sta else ''}&level=channel&format=text[/red]")
            else:
                autocomplete = self.query_one("#channels")
                autocomplete.items = [DropdownItem(unique) for unique in {c.split('|')[3] for c in r.text.splitlines()[1:]}]


    def action_unfocus_input(self) -> None:
        """An action to lose focus from input"""
        for item in self.query():
            item.blur()


if __name__ == "__main__":
    app = AvailabilityUI()
    app.run()
