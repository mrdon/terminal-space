import logging

logging.basicConfig(filename="/tmp/terminal-space-client.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


log = logging.getLogger("ts")
