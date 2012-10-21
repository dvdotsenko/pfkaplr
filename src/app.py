# -*- coding: utf-8 -*-
import logging

from taskhive import TaskHiveCoordinator
from components import APP_NAME
from components import events
from functools import partial as bind

class Application(object):
    def __init__(self):
        self.thc = TaskHiveCoordinator()

def exit_the_main_loop(exit_event):
    exit_event.set()

def main():
    import threading
    ev = threading.Event()
    ev.clear()

    events.subscribe(
        'Application.Exit'
        , bind(exit_the_main_loop, ev)
    )

    a = Application()
    
    print("\n# Press 'abort' key combination (usually CTRL+C) to stop the %s server #\n" % APP_NAME)
    try:
        while not ev.is_set():
            logging.debug("Main Loop...")
            ev.wait(30)
    except KeyboardInterrupt:
        pass

    print "Good bye"

if __name__ == '__main__':
    logging.getLogger().level = logging.DEBUG
    main()
