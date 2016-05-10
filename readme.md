This is a simple TradeWars clone that was inspired by http://blog.brianseitel.com/2015/07/07/tradewars-big-bang/

It only implements the basics of a universe, sectors, and ports, and probably won't be taken any farther.

To run it, install Python 3.5 and enter:

    python3.5 -m venv venv
    venv/bin/pip install -r requirements.txt
    venv/bin/python textapp.py

The other apps are:

  * rawapp.py - A raw json command interface.  Run via

      venv/bin/python script.py | venv/bin/python rawapp.py

  * webapp.py - A websocket-based web terminal interface
  * textapp.py - A local console interface