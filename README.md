# Terminal Space - a text-based space game

This is currently command line TradeWars clone that was inspired by 
http://blog.brianseitel.com/2015/07/07/tradewars-big-bang/

It currently implements the basics of a universe, sectors, and ports, 
but will soon be taken in new directions.

To run it, install Python 3.7 and run:

    pip3 install terminal-space

To install it locally, run:

    make virtualenv
    make run

To run the server standalone (needed for the "Join Game" option), run:

    make run-server
    
   
To run it in a clean docker container, run:

    make run-docker