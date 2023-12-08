from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Select, Input, Checkbox, Button, DataTable, Header
from textual.coordinate import Coordinate
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem
import requests
from datetime import datetime, timedelta
from typing import List
from rich.text import Text


# TODOS:
#  - how to lose focus from all elements
#  - find what to do with timestamps in lines
#  - implememnt bindings (up and down arrows reserved for scrolling, use tab and shift+tab instead): pending /, pageUp, pageDown, Enter
#  - see the issues
#  - write explanations and available buttons
#  - could have all nslc labels in a Container and the same for lines and then these containers into a Horizontal
#  - could make new classes of inputs and selections to make them smaller in height to have a smaller request control box

# PROBLEMS WITH AVAILABILITY:
#  - ORDER OF ROWS RETURNED FROM AVAILABILITY NOT ACCORDING TO TIME AND OVERLAP (see https://eida.koeri.boun.edu.tr/fdsnws/availability/1/query?&network=KO&station=ADVT&starttime=2023-12-06T00:27:16&endtime=2023-12-08T00:27:16)
#  - DUPLICATE ENTRIES (see https://eida.gein.noa.gr/fdsnws/availability/1/query?station=ATH&starttime=2023-12-02T00:27:16&endtime=2023-12-08T00:27:16)


class CursoredText(Input):
    """Widget that shows a Static text with a cursor that can be moved within text content"""

    DEFAULT_CSS = """
    CursoredText {
        background: $background;
        padding: 0 0;
        border: none;
        height: 1;
    }
    CursoredText:focus {
        border: none;
    }
    CursoredText>.input--cursor {
        background: $surface;
        color: $text;
        text-style: reverse;
    }
    """

    enriched = ""
    info = []

    def __init__(self, value=None, info=[], name=None, id=None, classes=None, disabled=False):
        super().__init__(value=Text.from_markup(value).plain, name=name, id=id, classes=classes, disabled=disabled)
        self.enriched = value
        self.info = info

    @property
    def _value(self) -> Text:
        """Value rendered as rich renderable"""
        return Text.from_markup(self.enriched)

    async def _on_key(self, event: events.Key) -> None:
        if event.is_printable:
            if event.character == 'C':
                nslc = self.parent.query_one(Label).renderable.split('_')
                self.parent.parent.parent.query_one("#network").value = str(nslc[0])
                self.parent.parent.parent.query_one("#station").value = str(nslc[1])
                self.parent.parent.parent.query_one("#location").value = str(nslc[2])
                self.parent.parent.parent.query_one("#channel").value = str(nslc[3])
            elif event.character == 'S':
                self.parent.parent.parent.query_one("#start").value = self.info[self.cursor_position][1]
            elif event.character == 'E':
                self.parent.parent.parent.query_one("#end").value = self.info[self.cursor_position][1]
            elif event.character == 'n':
                temp = self.value.find(' ', self.cursor_position)
                if temp > -1 and temp + 1 <= len(self.value):
                    self.cursor_position = temp + 1
                    if self.info[self.cursor_position][0]:
                        self.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
                    else:
                        self.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
            elif event.character == 'p':
                temp = self.value.rfind(' ', 0, self.cursor_position)
                if temp > -1 and temp - 1 >= 0:
                    temp = self.value.rfind(' ', 0, temp)
                    if temp > -1 and temp - 1 >= 0:
                        self.cursor_position = temp + 1
                    elif temp == -1 and self.cursor_position > 0:
                        self.cursor_position = 0
                    if self.info[self.cursor_position][0]:
                        self.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
                    else:
                        self.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
            event.stop()
            assert event.character is not None
            event.prevent_default()

    def _on_focus(self, event: events.Focus) -> None:
        self.cursor_position = 0
        if self.cursor_blink:
            self._blink_timer.resume()
        self.app.cursor_position = self.cursor_screen_offset
        self.has_focus = True
        self.refresh()
        if self.parent is not None:
            self.parent.post_message(events.DescendantFocus(self))
        if self.info[self.cursor_position][0]:
            self.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
        else:
            self.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
        event.prevent_default()

    def _on_paste(self, event: events.Paste) -> None:
        event.stop()
        event.prevent_default()

    def action_cursor_right(self) -> None:
        super().action_cursor_right()
        if self.info[self.cursor_position][0]:
            self.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
        else:
            self.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")

    def action_cursor_left(self) -> None:
        super().action_cursor_left()
        if self.info[self.cursor_position][0]:
            self.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
        else:
            self.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")

    def action_delete_right(self) -> None:
        pass

    def action_delete_right_word(self) -> None:
        pass

    def action_delete_right_all(self) -> None:
        pass

    def action_delete_left(self) -> None:
        pass

    def action_delete_left_word(self) -> None:
        pass

    def action_delete_left_all(self) -> None:
        pass


class Requests(Static):
    """Web service request control widget"""

    def compose(self) -> ComposeResult:
        yield Static("Requests control", id="request-title")
        yield Container(
            Horizontal(
                Label("Node:", classes="request-label", id="node-label"),
                Select([
                    ("NOA", "https://eida.gein.noa.gr/fdsnws/"),
                    ("RESIF", "https://ws.resif.fr/fdsnws/"),
                    ("ODC", "https://orfeus-eu.org/fdsnws/"),
                    ("GFZ", "https://geofon.gfz-potsdam.de/fdsnws/"),
                    ("INGV", "https://webservices.ingv.it/fdsnws/"),
                    ("ETHZ", "https://eida.ethz.ch/fdsnws/"),
                    ("BGR", "https://eida.bgr.de/fdsnws/"),
                    ("NIEP", "https://eida-sc3.infp.ro/fdsnws/"),
                    ("KOERI", "https://eida.koeri.boun.edu.tr/fdsnws/"),
                    ("LMU", "https://erde.geophysik.uni-muenchen.de/fdsnws/"),
                    ("UIB-NORSAR", "https://eida.geo.uib.no/fdsnws/"),
                    ("ICGC", "https://ws.icgc.cat/fdsnws/")
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
            Input(classes="date-input", id="start", value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")),
            Label("End Time:", classes="request-label"),
            Input(classes="date-input", id="end", value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
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
            Checkbox("Overlap", id="overlap", value=True),
            id="merge"
        )
        yield Horizontal(
            Label("Mergegaps:", classes="request-label"),
            Input(value="0.0", type="number", classes="short-input", id="mergegaps"),
            Label("Quality:", classes="request-label"),
            Checkbox("D", True, id="qd"),
            Checkbox("R", True, id="qr"),
            Checkbox("Q", True, id="qq"),
            Checkbox("M", True, id="qm"),
            id="gaps-quality"
        )


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield Static("Status")
        yield Static("", id="status-line")


class Results(Static):
    """Show results widget"""

    def compose(self) -> ComposeResult:
        yield Static("Results")


class AvailabilityUI(App):
    CSS_PATH = "availability_ui.css"
    BINDINGS = [("escape", "unfocus_input", "Lose input focus"),]

    def compose(self) -> ComposeResult:
        self.title = "Availability UI"
        yield Header()
        yield ScrollableContainer(
            Static("Explanations", classes="box"),
            Requests(classes="box"),
            Status(classes="box"),
            Results(classes="box", id="results-widget")
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
            mergegaps = self.query_one("#mergegaps")
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
                mergegaps.value = "1.0"
            elif event.value == 4:
                start.value = datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
                if datetime.now().date().day > 7:
                    mergegaps.value = "5.0"
            elif event.value == 5:
                start.value = (datetime.now() - timedelta(days=61)).strftime("%Y-%m-%dT%H:%M:%S")
                mergegaps.value = "10.0"
            elif event.value == 6:
                start.value = (datetime.now() - timedelta(days=183)).strftime("%Y-%m-%dT%H:%M:%S")
                mergegaps.value = "60.0"
            elif event.value == 7:
                start.value = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
                if datetime.now().date().month >= 6:
                    mergegaps.value = "300.0"
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
            # clear previous results
            if self.query('#info-bar'):
                self.query_one('#info-bar').remove()
            for r in self.query('.result-container'):
                r.remove()
            # build request
            node = self.query_one("#nodes").value if self.query_one("#nodes").value != Select.BLANK else None
            net = self.query_one("#network").value
            sta = self.query_one("#station").value
            loc = self.query_one("#location").value
            cha = self.query_one("#channel").value
            start = self.query_one("#start").value
            end = self.query_one("#end").value
            merge = ",".join([option for option, bool in zip(['samplerate', 'quality', 'overlap'], [self.query_one("#samplerate").value, self.query_one("#qual").value, self.query_one("#overlap").value]) if bool])
            mergegaps = str(self.query_one("#mergegaps").value)
            quality = ",".join([q for q, bool in zip(['D', 'R', 'Q', 'M'], [self.query_one("#qd").value, self.query_one("#qr").value, self.query_one("#qq").value, self.query_one("#qm").value]) if bool])
            request = f"{node+'availability/1/query' if node else self.query_one('#baseurl').value}?format=geocsv{'&network='+net if net else ''}{'&station='+sta if sta else ''}{'&location='+loc if loc else ''}{'&channel='+cha if cha else ''}{'&starttime='+start if start else ''}{'&endtime='+end if end else ''}{'&merge='+merge if merge else ''}{'&quality='+quality if quality else ''}{'&mergegaps='+mergegaps if mergegaps else ''}"
            self.query_one('#status-line').update("Issuing request "+request)
            try:
                r = requests.get(request)
            except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError):
                self.query_one("#status-line").update("[red]Please provide a valid availability URL[/red]")
                return None
            if r.status_code == 204:
                self.query_one('#status-line').update("[red]No data available[/red]")
            elif r.status_code != 200:
                self.query_one('#status-line').update(f"[red]{r.text}[/red]")
            else:
                self.query_one('#status-line').update(f"[green]Request successfully returned data from {request}[/green]")
                self.show_results(r.text.splitlines()[5:])


    def show_results(self, csv_results):
        infoBar = Static("Quality:     Timestamp:                       Trace start:                       Trace end:                    ", id="info-bar")
        self.query_one('#results-widget').mount(infoBar)
        # cut time frame into desired number of spans to see for how many of them a trace lasts
        num_spans = 130
        start_frame = datetime.strptime(self.query_one("#start").value, "%Y-%m-%dT%H:%M:%S")
        end_frame = datetime.strptime(self.query_one("#end").value, "%Y-%m-%dT%H:%M:%S")
        span_frame = (end_frame - start_frame).total_seconds() / num_spans
        traces = {} # for lines
        infos = {} # for the info-bar
        for row in csv_results:
            parts = row.split('|')
            key = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
            start_trace = datetime.strptime(parts[6], "%Y-%m-%dT%H:%M:%S.%fZ")
            end_trace = datetime.strptime(parts[7], "%Y-%m-%dT%H:%M:%S.%fZ")
            spans_trace = (end_trace - start_trace).total_seconds() / span_frame
            spans_trace = 1 if spans_trace < 1 else round(spans_trace)
            if parts[4] == 'D':
                traces[key] = traces.get(key, "") + "[yellow]" + "─"*spans_trace + "[/yellow]" + " "
            elif parts[4] == 'R':
                traces[key] = traces.get(key, "") + "[grey37]" + "─"*spans_trace + "[/gray37]" + " "
            elif parts[4] == 'Q':
                traces[key] = traces.get(key, "") + "[orchid]" + "─"*spans_trace + "[/orchid]" + " "
            elif parts[4] == 'M':
                traces[key] = traces.get(key, "") + "[cyan]" + "─"*spans_trace + "[/cyan]" + " "
            infos[key] = infos.get(key, []) + [(parts[4], "some_timestamp     " , parts[6][:19], parts[7][:19]) for st in range(spans_trace)] + [("", "", "", "")]
        for k in traces:
            traces[k] = traces[k][:-1] # remove last space
            self.query_one('#results-widget').mount(Horizontal(Label(k), CursoredText(value=traces[k], info=infos[k], classes="result-item"), classes="result-container", id=k))
        if self.query(".result-item"):
            self.query(".result-item")[0].focus()


    def action_unfocus_input(self) -> None:
        """An action to lose focus from input"""
        for item in self.query():
            item.blur()


if __name__ == "__main__":
    app = AvailabilityUI()
    app.run()
