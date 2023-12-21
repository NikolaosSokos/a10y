# a10y

The current repository hosts a user interface terminal application for the Availability webservice.

The application is mainly built using [textual](https://textual.textualize.io/) library for making terminal applications.


## Installation

The application can be installed on every system using [pyinstaller](https://pyinstaller.org/en/stable/).

It has been tested in an Ubuntu machine with pyinstaller version 6.3.0.

To install pyinstaller execute:
```
pip install pyinstaller
```

Clone from GitHub and move into project folder:
```
git clone https://github.com/EIDA/a10y.git
cd a10y
```

Execute pyinstaller as below:
```
pyinstaller --onefile --add-data "availability_ui.css:." availability_ui.py
```

These will create:
 - an `availability_ui.spec` file
 - a `build` folder
 - a `dist` folder

 Into `dist` folder you can find the final executable. By executing through terminal it opens the application:
```
./dist/availability_ui
```
