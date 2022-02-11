import asyncio
import sys

import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

# This is to prevent running engine process that Pycharm is no longer using
# In seconds
disconnection_deadline = 100
significant_sleep_time = timedelta(seconds=disconnection_deadline*2)


class ConnectionWatchdog:
    def __init__(self):
        self.last_wakeup = datetime.now()
        self.connected_clients = 0
        self.initial_connection_established = False

    def connection_established(self):
        logger.info(f'ConnectionWatchdog->connection_established')
        self.connected_clients += 1
        self.initial_connection_established = True

    def connection_lost(self):
        logger.info(f'ConnectionWatchdog->connection_lost')
        self.connected_clients -= 1

    async def watch_client_connection_loop(self):
        logger.info(f'started ConnectionWatchdog->watch_client_connection_loop')

        # if client was not reconnected in 100 seconds deadline - kill engine
        self.last_wakeup = datetime.now()
        while True:
            logger.debug(f'watch_client_connection_loop-> deciding if we need to close engine')
            await asyncio.sleep(disconnection_deadline)
            now = datetime.now()
            time_interval = now - self.last_wakeup
            logger.debug(f'  last wakeup {str(time_interval)} ago')
            logger.debug(f'  at {datetime.now().time()}')
            self.last_wakeup = now
            if time_interval > significant_sleep_time:
                logger.info('watch_client_connection_loop > significant_sleep_time elapsed, will skip next loop')
                # Probably PC wake up from sleep mode.
                # Sleep one more loop before making decision to terminate
                # Allow client plugins more time to reconnect
                continue

            if self.initial_connection_established and self.connected_clients <= 0:
                logger.warning('!! No connection established within reconnection deadline')
                logger.warning('Engine will exit. Please restart it again if you need to.')
                sys.exit(1)


connection_watchdog = ConnectionWatchdog()
