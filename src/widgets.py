from textual.widgets import Static, Input, Button, Label, Select, Collapsible, Checkbox, SelectionList
from textual.containers import Container

from textual.app import App, ComposeResult
class Explanations(Static):
    """Explanations box with common key functions"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Useful Keys[/b]")
        yield Static(
            """[gold3]ctrl+c[/gold3]: close app  [gold3]tab/shif+tab[/gold3]: cycle through options  [gold3]ctrl+s[/gold3]: send request  [gold3]esc[/gold3]: cancel request
            [gold3]up/down/pgUp/pgDown[/gold3]: scroll up/down if in scrollable window""",
            id="explanations-keys")


class Requests(Static):
    def __init__(self, nodes_urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nodes_urls = nodes_urls  # Store nodes for later use
    def compose(self) -> ComposeResult:
        yield Static("[b]Requests Control[/b]", id="request-title")
        yield Container(
            Checkbox("Select all Nodes", True, id="all-nodes"),
            SelectionList(*self.nodesUrls, id="nodes"),
            id="nodes-container"
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
            Label("Mergegaps:", classes="request-label"),
            Input(value=default_mergegaps, type="number", id="mergegaps"),
            Label("Merge Options:", classes="request-label"),
            Checkbox("Samplerate", default_merge_samplerate, id="samplerate"),
            Checkbox("Quality", default_merge_quality, id="qual"),
            Checkbox("Overlap", default_merge_overlap, id="overlap"),
            Label("Quality:", classes="request-label"),
            Checkbox("D", default_quality_D, id="qd"),
            Checkbox("R", default_quality_R, id="qr"),
            Checkbox("Q", default_quality_Q, id="qq"),
            Checkbox("M", default_quality_M, id="qm"),
            id="options"
        )
        yield Horizontal(
            Checkbox("Include Restricted", default_includerestricted, id="restricted"),
            Button("Send", variant="primary", id="request-button"),
            Input(placeholder="Enter POST file path", value=default_file, suggester=FileSuggester(), id="post-file"),
            Button("File", variant="primary", id="file-button"),
            id="send-request"
        )


class Status(Static):
    """Status line to show user what request is currently issued"""

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(Static(f'Welcome to Availability UI application version 1.0! 🙂\nCurrent session started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', id="status-line"), id="status-container")


class Results(Static):
    """Show results widget"""

    def compose(self) -> ComposeResult:
        yield Static("[b]Results[/b]")
        yield LoadingIndicator(classes="hide", id="loading")
        yield Static(id="error-results", classes="hide")
