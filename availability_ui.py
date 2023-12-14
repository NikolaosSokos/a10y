from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Select, Input, Checkbox, Button, ContentSwitcher, Header
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem
import requests
from datetime import datetime, timedelta
from rich.text import Text
from rich.cells import get_character_cell_size
import os
import sys
import logging


# TODOS:
#  - implememnt / binding
#  - see the issues
#  - possible bad thing: in case long gap ends in middle of span and trace starts I print a dash as if there was no gap
#  - too few results => extra space in results up to height 30, making height auto => no scrollbar when many results


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
                nslc = self.id.split('_')
                self.parent.parent.parent.parent.parent.parent.query_one("#network").value = str(nslc[0])
                self.parent.parent.parent.parent.parent.parent.query_one("#station").value = str(nslc[1])
                self.parent.parent.parent.parent.parent.parent.query_one("#location").value = str(nslc[2])
                self.parent.parent.parent.parent.parent.parent.query_one("#channel").value = str(nslc[3])
            elif event.character == 'S':
                self.parent.parent.parent.parent.parent.parent.query_one("#start").value = self.info[self.cursor_position][1]
            elif event.character == 'E':
                self.parent.parent.parent.parent.parent.parent.query_one("#end").value = self.info[self.cursor_position][1]
            elif event.character == 'n':
                temp1 = self.value.find(' ', self.cursor_position)
                temp2 = self.value.find('╌', self.cursor_position)
                temp3 = self.value.find('┄', self.cursor_position)
                if max(temp1, temp2, temp3) != -1:
                    temp = min([n for n in (temp1, temp2, temp3) if n >= 0])
                    temp = self.value.find('─', temp)
                    if temp != -1:
                        self.cursor_position = temp
                        if self.info[self.cursor_position][1]:
                            if self.value[self.cursor_position] == '─':
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
                            elif self.value[self.cursor_position] == ' ':
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
                            else:
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
                        else:
                            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
            elif event.character == 'p':
                temp1 = self.value.rfind(' ', 0, self.cursor_position)
                temp2 = self.value.rfind('╌', 0, self.cursor_position)
                temp3 = self.value.rfind('┄', 0, self.cursor_position)
                temp = max(temp1, temp2, temp3)
                if temp != -1:
                    temp = self.value.rfind('─', 0, temp)
                    if temp != -1:
                        temp1 = self.value.rfind(' ', 0, temp)
                        temp2 = self.value.rfind('╌', 0, temp)
                        temp3 = self.value.rfind('┄', 0, temp)
                        temp = max(temp1, temp2, temp3)
                        if temp == -1:
                            self.cursor_position = 0
                        else:
                            self.cursor_position = temp + 1
                        if self.info[self.cursor_position][1]:
                            if self.value[self.cursor_position] == '─':
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
                            elif self.value[self.cursor_position] == ' ':
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
                            else:
                                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
                        else:
                            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
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
        if self.info[self.cursor_position][1]:
            if self.value[self.cursor_position] == '─':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
            elif self.value[self.cursor_position] == ' ':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
            else:
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
        else:
            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")
        event.prevent_default()

    def _on_paste(self, event: events.Paste) -> None:
        event.stop()
        event.prevent_default()

    def action_cursor_right(self) -> None:
        super().action_cursor_right()
        if self.info[self.cursor_position][1]:
            if self.value[self.cursor_position] == '─':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
            elif self.value[self.cursor_position] == ' ':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
            else:
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
        else:
            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")

    def action_cursor_left(self) -> None:
        super().action_cursor_left()
        if self.info[self.cursor_position][1]:
            if self.value[self.cursor_position] == '─':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
            elif self.value[self.cursor_position] == ' ':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
            else:
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
        else:
            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")

    async def _on_click(self, event: events.Click) -> None:
        offset = event.get_content_offset(self)
        if offset is None:
            return
        event.stop()
        click_x = offset.x + self.view_position
        cell_offset = 0
        _cell_size = get_character_cell_size
        for index, char in enumerate(self.value):
            cell_width = _cell_size(char)
            if cell_offset <= click_x < (cell_offset + cell_width):
                self.cursor_position = index
                break
            cell_offset += cell_width
        else:
            self.cursor_position = len(self.value)
        if self.info[self.cursor_position][1]:
            if self.value[self.cursor_position] == '─':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start: {self.info[self.cursor_position][2]}   Trace end: {self.info[self.cursor_position][3]} ")
            elif self.value[self.cursor_position] == ' ':
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Quality:     Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
            else:
                self.parent.parent.parent.parent.parent.query_one("#info-bar").update(f"Gaps: {self.info[self.cursor_position][0]}   Timestamp: {self.info[self.cursor_position][1]}   Trace start:                       Trace end:                    ")
        else:
            self.parent.parent.parent.parent.parent.query_one("#info-bar").update("Quality:     Timestamp:                       Trace start:                       Trace end:                    ")

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


class Explanations(Static):
    """Explanations box with common key functions"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Useful Keys[/b] ([violet]purple[/violet] key bindings can be used if results are shown on the results window)")
        yield Static(
"""[gold3]ctrl+b[/gold3]: focus button             [gold3]enter[/gold3]: send request if button is focused   [gold3]tab/shif+tab[/gold3]: focus next/previous item or channel
[violet]ctrl+v[/violet]: change results view      [violet]ctrl+t/ctrl+l[/violet]: jump to first/last channel  [gold3]up/down/pgUp/pgDown[/gold3]: scroll up/down if in a scrollable item
[violet]right/left[/violet]: move cursor on line  [violet]home/end[/violet]: jump to beginning/end of line    [violet]S[/violet]: capture timestamp under cursor as Start Time
[violet]C[/violet]: capture NSLC under cursor     [violet]n/p[/violet]: jump to next/previous trace of line   [violet]E[/violet]: capture timestamp under cursor as End Time  [gold3]ctrl+c[/gold3]: close app""",
            id="explanations-keys")


class Requests(Static):
    """Web service request control widget"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Requests Control[/b]", id="request-title")
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
            Input(classes="date-input", id="start", value=default_starttime),
            Label("End Time:", classes="request-label"),
            Input(classes="date-input", id="end", value=default_endtime),
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
            Checkbox("Samplerate", default_merge_samplerate, id="samplerate"),
            Checkbox("Quality", default_merge_quality, id="qual"),
            Checkbox("Overlap", default_merge_overlap, id="overlap"),
            id="merge"
        )
        yield Horizontal(
            Label("Mergegaps:", classes="request-label"),
            Input(value=default_mergegaps, type="number", classes="short-input", id="mergegaps"),
            Label("Quality:", classes="request-label"),
            Checkbox("D", default_quality_D, id="qd"),
            Checkbox("R", default_quality_R, id="qr"),
            Checkbox("Q", default_quality_Q, id="qq"),
            Checkbox("M", default_quality_M, id="qm"),
            id="gaps-quality"
        )


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Status[/b]")
        yield ScrollableContainer(Static(f'Current session started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', id="status-line"), id="status-container")


class Results(Static):
    """Show results widget"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Results[/b]")


class AvailabilityUI(App):
    CSS_PATH = "availability_ui.css"
    BINDINGS = [
        ("ctrl+t", "first_line", "Move to first line"),
        ("ctrl+l", "last_line", "Move to last line"),
        ("ctrl+b", "button_focus", "Focus button"),
        ("ctrl+v", "change_result_view", "Change result view"),
    ]

    def compose(self) -> ComposeResult:
        self.title = "Availability UI"
        yield Header()
        yield ScrollableContainer(
            Explanations(classes="box"),
            Requests(classes="box"),
            Status(classes="box"),
            Results(classes="box", id="results-widget"),
            id="application-container"
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """A function to issue appropriate request and update status when a Node or when a common time frame is selected"""
        if event.select == self.query_one("#nodes"):
            if event.value and self.query_one("#nodes").value != Select.BLANK:
                self.query_one("#baseurl").add_class("hide") # hide user typing URL input if has chosen to select from dropdown
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\nChecking {event.value}availability/1/query')
                self.query_one("#status-container").scroll_end()
                r = requests.get(event.value+"availability/1/query")
                if 'availability' in r.text:
                    # get available networks from FDSN
                    self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\nRetrieving Networks from {event.value}station/1/query?level=network&format=text')
                    self.query_one("#status-container").scroll_end()
                    r = requests.get(event.value+"station/1/query?level=network&format=text")
                    if r.status_code != 200:
                        self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Couldn\'t retrieve Networks from {event.value}station/1/query?level=network&format=text[/red]')
                        self.query_one("#status-container").scroll_end()
                    else:
                        self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[green]Retrieved Networks from {event.value}station/1/query?level=network&format=text[/green]')
                        self.query_one("#status-container").scroll_end()
                        autocomplete_nets = self.query_one("#networks")
                        autocomplete_nets.items = [DropdownItem(n.split('|')[0]) for n in r.text.splitlines()[1:]]
                else:
                    self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Availability URL is not valid[/red]')
                    self.query_one("#status-container").scroll_end()
            else:
                self.query_one("#baseurl").remove_class("hide") # show input for typing URL if user does not want to select from dropdown
                self.query_one("#status-container").scroll_end()

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
            self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\nChecking {event.value}')
            self.query_one("#status-container").scroll_end()
            try:
                r = requests.get(event.value)
            except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Invalid availability URL[/red]')
                self.query_one("#status-container").scroll_end()
                return None
            if r.status_code == 400 and 'availability' in r.text:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[green]Valid availability URL[/green]')
                self.query_one("#status-container").scroll_end()
            else:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Invalid availability URL[/red]')
                self.query_one("#status-container").scroll_end()
        # for typing network
        elif event.input == self.query_one("#network"):
            # handle case of submitting without having selected Node
            if self.query_one('#nodes').value is None:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Please select a Node[/red]')
                self.query_one("#status-container").scroll_end()
                return None
            # get available stations from FDSN
            net = self.query_one('#network').value
            self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\nRetrieving Stations from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}&format=text')
            self.query_one("#status-container").scroll_end()
            r = requests.get(f"{self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}&format=text")
            if r.status_code != 200:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Couldn\'t retrieve Stations from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}&format=text[/red]')
                self.query_one("#status-container").scroll_end()
            else:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[green]Retrieved Stations from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}&format=text[/green]')
                self.query_one("#status-container").scroll_end()
                autocomplete = self.query_one("#stations")
                autocomplete.items = [DropdownItem(s.split('|')[1]) for s in r.text.splitlines()[1:]]
        # for typing station
        elif event.input == self.query_one("#station"):
            # handle case of submitting without having selected Node
            if self.query_one('#nodes').value is None:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Please select a Node[/red]')
                self.query_one("#status-container").scroll_end()
                return None
            # get available channels from FDSN
            net = self.query_one('#network').value
            sta = self.query_one('#station').value
            self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\nRetrieving Channels from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}{"&station="+sta if sta else ""}&level=channel&format=text')
            self.query_one("#status-container").scroll_end()
            r = requests.get(f"{self.query_one('#nodes').value}station/1/query?{'network='+net if net else ''}{'&station='+sta if sta else ''}&level=channel&format=text")
            if r.status_code != 200:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Couldn\'t retrieve Channels from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}{"&station="+sta if sta else ""}&level=channel&format=text[/red]')
                self.query_one("#status-container").scroll_end()
            else:
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[green]Retrieved Channels from {self.query_one("#nodes").value}station/1/query?{"network="+net if net else ""}{"&station="+sta if sta else ""}&level=channel&format=text[/green]')
                self.query_one("#status-container").scroll_end()
                autocomplete = self.query_one("#channels")
                autocomplete.items = [DropdownItem(unique) for unique in {c.split('|')[3] for c in r.text.splitlines()[1:]}]


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """A function to send availability request when Send button is clicked"""
        if event.button == self.query_one("#request-button"):
            # clear previous results
            if self.query(ContentSwitcher):
                self.query_one(ContentSwitcher).remove()
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
            self.query_one('#status-line').update(f'{self.query_one("#status-line").renderable}\nIssuing request {request}')
            self.query_one("#status-container").scroll_end()
            try:
                r = requests.get(request)
            except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError):
                self.query_one("#status-line").update(f'{self.query_one("#status-line").renderable}\n[red]Please provide a valid availability URL[/red]')
                self.query_one("#status-container").scroll_end()
                return None
            if r.status_code == 204:
                self.query_one('#status-line').update(f'{self.query_one("#status-line").renderable}\n[red]No data available[/red]')
                self.query_one("#status-container").scroll_end()
            elif r.status_code != 200:
                self.query_one('#status-line').update(f'{self.query_one("#status-line").renderable}\n[red]{r.text}[/red]')
                self.query_one("#status-container").scroll_end()
            else:
                self.query_one('#status-line').update(f'{self.query_one("#status-line").renderable}\n[green]Request successfully returned data[/green]')
                self.query_one("#status-container").scroll_end()
                self.show_results(r.text)


    def show_results(self, csv_results):
        self.query_one('#results-widget').mount(ContentSwitcher(Container(id="lines"), ScrollableContainer(Static(csv_results, id="plain"), id="plain-container"), initial="lines"))
        infoBar = Static("Quality:     Timestamp:                       Trace start:                       Trace end:                    ", id="info-bar")
        self.query_one('#lines').mount(infoBar)
        self.query_one('#lines').mount(ScrollableContainer(id="results-container"))
        # cut time frame into desired number of spans to see for how many of them a trace lasts
        num_spans = 130
        start_frame = datetime.strptime(self.query_one("#start").value, "%Y-%m-%dT%H:%M:%S")
        end_frame = datetime.strptime(self.query_one("#end").value, "%Y-%m-%dT%H:%M:%S")
        span_frame = (end_frame - start_frame) / num_spans
        lines = {} # for lines of each nslc
        infos = {} # for the info-bar of each nslc
        csv_results = csv_results.splitlines()[5:]
        for span in range(num_spans):
            # find traces and quality codes (U for undefined, i.e. initialization or traces with different codes exist)
            # for each span of each nslc line
            traces_qual = {}
            for i, row in enumerate(csv_results):
                parts = row.split('|')
                key = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
                start_trace = datetime.strptime(parts[6], "%Y-%m-%dT%H:%M:%S.%fZ")
                end_trace = datetime.strptime(parts[7], "%Y-%m-%dT%H:%M:%S.%fZ")
                traces_qual[key] = traces_qual.get(key, [[], 'U']) # initialization
                span_start = start_frame + span * span_frame
                span_end = start_frame + (span + 1) * span_frame
                # below condition explained: if trace has at least a part of it into the current span
                if (span_start <= start_trace < span_end or
                    span_start < end_trace <= span_end or
                    start_trace <= span_start < span_end <= end_trace):
                    traces_qual[key][0].append(i) # row i has a part into span
                    if len(traces_qual[key][0]) == 1:
                        traces_qual[key][1] = parts[4] # first trace for span gives quality code
                    else:
                        traces_qual[key][1] = 'U' # if more traces in one span => undefined quality code
            # write current span for each nslc line
            for key in traces_qual:
                lines[key] = lines.get(key, "") # initialization
                infos[key] = infos.get(key, []) # initialization
                if len(traces_qual[key][0]) == 0:
                    lines[key] += ' '
                    infos[key].append(("", (start_frame+(span+0.5)*span_frame).strftime("%Y-%m-%dT%H:%M:%S"), "", ""))
                elif len(traces_qual[key][0]) == 1:
                    if traces_qual[key][1] == 'D':
                        lines[key] += "[yellow]─[/yellow]"
                    elif traces_qual[key][1] == 'R':
                        lines[key] += "[green1]─[/green1]"
                    elif traces_qual[key][1] == 'Q':
                        lines[key] += "[orchid]─[/orchid]"
                    elif traces_qual[key][1] == 'M':
                        lines[key] += "[cyan]─[/cyan]"
                    infos[key].append((traces_qual[key][1], (start_frame+(span+0.5)*span_frame).strftime("%Y-%m-%dT%H:%M:%S"), csv_results[traces_qual[key][0][0]].split('|')[6][:19], csv_results[traces_qual[key][0][0]].split('|')[7][:19]))
                elif len(traces_qual[key][0]) == 2:
                    lines[key] += '╌'
                    infos[key].append(("1", (start_frame+(span+0.5)*span_frame).strftime("%Y-%m-%dT%H:%M:%S"), "", ""))
                else:
                    lines[key] += '┄'
                    infos[key].append((str(len(traces_qual[key][0])-1), (start_frame+(span+0.5)*span_frame).strftime("%Y-%m-%dT%H:%M:%S"), "", ""))
        # find longest label to align start of lines
        longest_label = max([len(k) for k in lines.keys()])
        for k in lines:
            infos[k].append(("", "", "", "")) # because cursor can go one character after the end of the input
            self.query_one('#results-container').mount(Horizontal(Label(f"{k}{' '*(longest_label-len(k))}"), CursoredText(value=lines[k], info=infos[k], id=k), classes="result-item"))
        if self.query(CursoredText):
            self.query(CursoredText)[0].focus()


    def action_first_line(self) -> None:
        """An action to move focus to the first line"""
        if self.query(CursoredText):
            self.query(CursoredText)[0].focus()


    def action_last_line(self) -> None:
        """An action to move focus to the last line"""
        if self.query(CursoredText):
            self.query(CursoredText)[-1].focus()


    def action_button_focus(self) -> None:
        """An action to move focus to the button which sends request"""
        if self.query_one("#request-button"):
            self.query_one("#request-button").focus()


    def action_change_result_view(self) -> None:
        """An action to change result view between lines and plain text"""
        if self.query(ContentSwitcher):
            if self.query_one(ContentSwitcher).current == "lines":
                self.query_one(ContentSwitcher).current = "plain-container"
            else:
                self.query_one(ContentSwitcher).current = "lines"


if __name__ == "__main__":
    # use below defaults or take them from config file if exists
    default_starttime = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    default_endtime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    default_quality_D = True
    default_quality_R = True
    default_quality_Q = True
    default_quality_M = True
    default_mergegaps = "0.0"
    default_merge_samplerate = False
    default_merge_quality = False
    default_merge_overlap = True

    config_dir = os.getenv("XDG_CONFIG_DIR", ".")
    config_file = os.path.join(config_dir, "config.toml")
    if os.path.isfile(config_file):
        with open(config_file, 'r') as f:
            for line in f.readlines():
                parts = line.split()
                try:
                    x = parts[0]
                except:
                    continue
                if parts[0] == "starttime":
                    try:
                        num = int(parts[1])
                        default_starttime = (datetime.now() - timedelta(days=num)).strftime("%Y-%m-%dT%H:%M:%S")
                    except:
                        try:
                            datetime.strptime(parts[1], "%Y-%m-%dT%H:%M:%S")
                            default_starttime = parts[1]
                        except:
                            logging.error(f"Invalid starttime format in config file {config_file}")
                            sys.exit(1)
                elif parts[0] == "endtime":
                    if parts[1] == "now":
                        pass
                    else:
                        try:
                            datetime.strptime(parts[1], "%Y-%m-%dT%H:%M:%S")
                            default_endtime = parts[1]
                        except:
                            logging.error(f"Invalid endtime format in config file {config_file}")
                            sys.exit(1)
                elif parts[0] == "quality":
                    quals = parts[1].split(',')
                    if any([q not in ['D', 'R', 'Q', 'M'] for q in quals]):
                        logging.error(f"Invalid quality codes format in config file {config_file}")
                        sys.exit(1)
                    if 'D' not in quals:
                        default_quality_D = False
                    if 'R' not in quals:
                        default_quality_R = False
                    if 'Q' not in quals:
                        default_quality_Q = False
                    if 'M' not in quals:
                        default_quality_M = False
                elif parts[0] == "mergegaps":
                    try:
                        num = float(parts[1])
                    except:
                        logging.error(f"Invalid mergegaps format in config file {config_file}")
                        sys.exit(1)
                    default_mergegaps = str(num)
                elif parts[0] == "merge":
                    merges = parts[1].split(',')
                    if any([m not in ['samplerate', 'quality', 'overlap'] for m in merges]):
                        logging.error(f"Invalid merge options format in config file {config_file}")
                        sys.exit(1)
                    if 'samplerate' in merges:
                        default_merge_samplerate = True
                    if 'quality' in merges:
                        default_merge_quality = True
                    if 'overlap' not in merges:
                        default_merge_overlap = False
                else:
                    logging.error(f"Invalid default '{parts[0]}' in config file '{config_file}'")
                    sys.exit(1)

    app = AvailabilityUI()
    app.run()
