from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Select, Input, Checkbox, Button, DataTable, Header
from textual.coordinate import Coordinate
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem
import requests
from datetime import datetime, timedelta


# PENDINGS:
#  - URLs for all nodes
#  - how to lose focus from all elements
#  - find a way to have space between info-bar and table
#  - find a way to move the cursor into lines (maybe sufficient to have one column for each line)


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
            Input(placeholder="Enter Node Availability URL", id="baseurl"), # for the case of user entering availability endpoint URL
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
            Input(classes="date-input", id="start"),
            Label("End Time:", classes="request-label"),
            Input(classes="date-input", id="end"),
            Select([
                ("last 24 hours", 1),
                ("last 2 days", 2),
                ("last 7 days", 3),
                ("this month", 4),
                ("last 2 months", 5),
                ("last 6 months", 6),
                ("this year", 7)
                ], prompt="Common time frames", id="times"),
            id="timeframe"
        )
        yield Horizontal(
            Label("Merge Options:", classes="request-label"),
            Checkbox("Samplerate", id="samplerate"),
            Checkbox("Quality", id="qual"),
            Checkbox("Overlap", id="overlap"),
            id="merge"
        )
        yield Horizontal(
            Label("Quality:", classes="request-label"),
            Checkbox("D", True, id="qd"),
            Checkbox("R", True, id="qr"),
            Checkbox("Q", True, id="qq"),
            Checkbox("M", True, id="qm"),
            id="quality"
        )


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield Static("Status")
        yield Static("", id="status-line")


class Results(Static):
    """App show results widget"""

    class MyDataTable(DataTable):
        def compose(self) -> ComposeResult:
            yield Static("     Quality:                     Timestamp:                     Trace start:                      Trace end:                     ", id="info-bar")

        def action_cursor_down(self) -> None:
            self.query_one("#info-bar").update("     Test...")
            super().action_cursor_down()

    def compose(self) -> ComposeResult:
        yield Static("Results")
        yield self.MyDataTable(show_header=True, id="results")


class AvailabilityUI(App):
    CSS_PATH = "availability_ui.css"
    BINDINGS = [("escape", "unfocus_input", "Lose input focus"),]

    def compose(self) -> ComposeResult:
        self.title = "Availability UI"
        yield Header("Availability UI")
        yield ScrollableContainer(
            Static("Explanations", classes="box"),
            Requests(classes="box"),
            Status(classes="box", id="status-widget"),
            Results(classes="box")
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """A function to issue appropriate request and update status when a Node or when a common time frame is selected"""
        if event.select == self.query_one("#nodes"):
            if event.value:
                self.query_one("#baseurl").add_class("hide") # hide user typing URL input if has chosen to select from dropdown
                self.query_one("#status-line").update(f"Checking {event.value}availability/1/query")
                r = requests.get(event.value+"availability/1/query")
                if 'availability' in r.text:
                    # get available networks from FDSN
                    self.query_one("#status-line").update(f'Retrieving Networks from {event.value}station/1/query?level=network&format=text')
                    r = requests.get(event.value+"station/1/query?level=network&format=text")
                    if r.status_code != 200:
                        self.query_one("#status-line").update(f"[red]Couldn't retrieve Networks from {event.value}station/1/query?level=network&format=text[/red]")
                    else:
                        self.query_one("#status-line").update(f'[green]Retrieved Networks from {event.value}station/1/query?level=network&format=text[/green]')
                        autocomplete_nets = self.query_one("#networks")
                        autocomplete_nets.items = [DropdownItem(n.split('|')[0]) for n in r.text.splitlines()[1:]]
                else:
                    self.query_one("#status-line").update('[red]Availability URL is not valid[/red]')
            else:
                self.query_one("#baseurl").remove_class("hide") # show input for typing URL if user does not want to select from dropdown
                self.query_one("#status-line").update("")

        if event.select == self.query_one("#times"):
            start = self.query_one("#start")
            if not event.value:
                start.value = ""
                end = self.query_one("#end")
                end.value = ""
                return None
            if event.value == 1:
                start.value = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 2:
                start.value = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 3:
                start.value = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 4:
                start.value = datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 5:
                start.value = (datetime.now() - timedelta(days=61)).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 6:
                start.value = (datetime.now() - timedelta(days=183)).strftime("%Y-%m-%dT%H:%M:%S")
            elif event.value == 7:
                start.value = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            end = self.query_one("#end")
            end.value = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


    def on_input_submitted(self, event: Input.Submitted) -> None:
        """A function to change status when an availability endpoint URL or an NSLC input field is submitted (i.e. is typed and enter is hit)"""
        # for typing availability endpoint URL
        if event.input == self.query_one("#baseurl"):
            self.query_one("#status-line").update("Checking "+event.value)
            try:
                r = requests.get(event.value)
            except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                self.query_one("#status-line").update("[red]Invalid availability URL[/red]")
                return None
            if r.status_code == 400 and 'availability' in r.text:
                self.query_one("#status-line").update("[green]Valid availability URL[/green]")
            else:
                self.query_one("#status-line").update("[red]Invalid availability URL[/red]")
        # for typing network
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
                self.query_one("#status-line").update(f"[green]Retrieved Stations from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}&format=text[/green]")
                autocomplete = self.query_one("#stations")
                autocomplete.items = [DropdownItem(s.split('|')[1]) for s in r.text.splitlines()[1:]]
        # for typing station
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
                self.query_one("#status-line").update(f"[green]Retrieved Channels from {self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}{'&station='+sta if sta else ''}&level=channel&format=text[/green]")
                autocomplete = self.query_one("#channels")
                autocomplete.items = [DropdownItem(unique) for unique in {c.split('|')[3] for c in r.text.splitlines()[1:]}]


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """A function to send availability request when Send button is clicked"""
        if event.button == self.query_one("#request-button"):
            node = self.query_one("#nodes").value
            net = self.query_one("#network").value
            sta = self.query_one("#station").value
            loc = self.query_one("#location").value
            cha = self.query_one("#channel").value
            start = self.query_one("#start").value
            end = self.query_one("#end").value
            merge = ",".join([option for option, bool in zip(['samplerate', 'quality', 'overlap'], [self.query_one("#samplerate").value, self.query_one("#qual").value, self.query_one("#overlap").value]) if bool])
            quality = ",".join([q for q, bool in zip(['D', 'R', 'Q', 'M'], [self.query_one("#qd").value, self.query_one("#qr").value, self.query_one("#qq").value, self.query_one("#qm").value]) if bool])
            request = f"{node+'availability/1/query' if node else self.query_one('#baseurl').value}?format=geocsv{'&network='+net if net else ''}{'&station='+sta if sta else ''}{'&location='+loc if loc else ''}{'&channel='+cha if cha else ''}{'&starttime='+start if start else ''}{'&endtime='+end if end else ''}{'&merge='+merge if merge else ''}{'&quality='+quality if quality else ''}"
            self.query_one('#status-line').update("Issuing request "+request)
            try:
                r = requests.get(request)
            except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                self.query_one("#status-line").update("[red]Please provide a valid availability URL[/red]")
                return None
            if r.status_code == 204:
                self.query_one('#status-line').update("[red]No data available[/red]")
            elif r.status_code != 200:
                self.query_one('#status-line').update(f"[red]{r.text}[/red]")
            else:
                self.query_one('#status-line').update("[green]Request successfully returned data![/green]")
                self.show_results(r.text.splitlines()[5:])


    def show_results(self, csv_results):
        rows = {}
        for r in csv_results:
            parts = r.split('|')
            key = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
            rows[key] = rows.get(key, "") + "─── "
        self.query_one("#results").clear()
        self.query_one("#results").add_columns("", "")
        self.query_one("#results").add_rows(list(rows.items()))
        self.query_one("#results").focus()


    def action_unfocus_input(self) -> None:
        """An action to lose focus from input"""
        for item in self.query():
            item.blur()


if __name__ == "__main__":
    app = AvailabilityUI()
    app.run()
