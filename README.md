# a10y

The current repository hosts a user interface terminal application for the Availability webservice.

The application is mainly built using [textual](https://textual.textualize.io/) library for making terminal applications.


## Installation

### As a binary (recommended)

You can download a10y in the release section, by choosing the binary that suits your system.

### In a python virtual environment 

Clone the sources, create a virtual environment, get dependencies and run as a python script:

```
git clone https://github.com/EIDA/a10y.git
cd a10y
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python a10y.py
```

### With conda

### With pyinstaller

This method is intended to provide a portable executable for the application.

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
pyinstaller --onefile --add-data "a10y.css:." a10y.py -n a10y
```

This will create:
 - an `a10y.spec` file
 - a `build` folder
 - a `dist` folder

 Into `dist` folder you can find the final executable. By executing through terminal it opens the application:
```
./dist/a10y
```

The application can be executed as every other executable in your system, for example:
```
./a10y
```

### Options

The application can be executed with the following options:
 - `-n or --node` followed by Node name to start the application using the specified Node for making requests to the availability webservice
 - `-p or --post` followed by path that points to a file to start the application using that file for making POST requests to availability webservice

### Configuration

A `config.toml` file with some default values for the parameters of the requests can be provided, so that the application starts with them as selected.

With the configuration file, you can set your default values for starttime, endtime, quality, mergegaps or merge policy.

The application looks for the configuration file in this order:

  - with the `-c` or `--config` command line option
  - in the `$XDG_CONFIG_DIR/a10y` directory
  - in the directory of the application script

## Customizing the layout

All the layout colors are described in a CSS file `a10y.css` that can be customized. This is not possible at the moment with the binary release, which embeds the CSS file.
