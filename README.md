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
pyinstaller --onefile --add-data "availability_ui.css:." availability_ui.py -n a10y
```

These will create:
 - an `a10y.spec` file
 - a `build` folder
 - a `dist` folder

 Into `dist` folder you can find the final executable. By executing through terminal it opens the application:
```
./dist/a10y
```

## Running the application

The application can be executed as every other executable in your system, for example:
```
./a10y
```

### Options

The application can be executed with the following options:
 - `-n or --node` followed by Node name to start the application using the specified Node for making requests to the availability webservice
 - `-p or --post` followed by path that points to a file to start the application using that file for making POST requests to availability webservice

### Defaults

A `config.toml` file with some default values for the parameters of the requests can be provided, so that the application starts with them as selected.

Such a file is included in the current repository as an example.

The file needs to be either in the same folder as the executable or its path has to be given be an environment variable like below:
```
XDG_CONFIG_DIR=/path/to/file ./a10y
```
