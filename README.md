# Terminal Space

Terminal Space is a text-based space trading and exploration game that was inspired by [TradeWars 2002](http://tradewars.com) and several other space trading, elite-type games such as [Space Trader](https://en.wikipedia.org/wiki/Space_Trader_(Palm_OS)) and [Space Rangers](https://en.wikipedia.org/wiki/Space_Rangers_(video_game)).

[![asciicast](https://asciinema.org/a/Rud50qG0utHbHBpHGl60WuRRX.svg)](https://asciinema.org/a/Rud50qG0utHbHBpHGl60WuRRX)

## Features

1. Full screen text-based interface
2. Single and multi-player modes (with standalone server)
3. TradeWars 2002 concepts like sectors, planets, ports, and ships

It currently implements the TradeWars basics of a universe, sectors, and ports, but will next be taken in new directions.

### Roadmap

 * 0.1 (released) - Basic client/server model with structured text ui and simple TW2002 gameplay
 * 0.2 - Explore turn-based combat ala JRPGs like Octopath.  Focus on game mechanics.
 * 0.3 - Server and client saving, maybe host a game
 * 0.4 - Who knows...
 
## Installation

To run it, install Python 3.7 and run:

    pip3 install terminal-space

## Running the game

With the game installed, simply run

    tspace-client

To run the server standalone (needed for the "Join Game" option), run:

    tspace-server
    
## Development 

To install it locally, run:

    make virtualenv
    source venv/bin/activate
 
To run the client, type:

    make run
    
You can see all the possible commands by running:

    make 
    
Development is occasionally streamed on my [Twitch stream](https://www.twitch.tv/mrdonbrown/) and I'm on twitter as @mrdonbrown.
