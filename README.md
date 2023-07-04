# A-bad-social-media
## Brief description
A very bad social media site that I made for one of my assignments in a course that I really hated.

## Credits
It was a collaborative effort between me and my groupmate Rason Liu. Unfortunately he does not have a github account so I cannot link him within this README.

## Prerequisites
All the prerequisites are listed within `requirements.txt`

It is recommended to install them within a python virtual environment as documented [here](https://docs.python.org/3/library/venv.html) in order to not mess with your system's libraries.

If you have `pip` then you can simply use the command.

``pip install -r requirements.txt``

If not then please install `pip`.


## Running the project

There is a gunicorn config file, the server can be run simply using the command

```
gunicorn project:app
```

You can also customise stuff within that config file (ie. bind to another port).

By default, I bind the site into address `127.0.0.1:5000` so just run the program then enter that into your browser.

## Features
To be added if I ever have the motivation to do so.