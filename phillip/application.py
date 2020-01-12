import asyncio
import signal
import sys
import traceback
from datetime import datetime, timedelta
from typing import List

from pyee import AsyncIOEventEmitter

from phillip import helper
from phillip.event_helper import get_events
from phillip.handlers import Handler, SimpleHandler

class Phillip:
    """Representation of Aiess client to interact with osu! web.
    This client will interact with osu! API and web through scraper.

    Parameters
    ----------
    token: str
        osu! API token, could be gathered `here <https://osu.ppy.sh/p/api>`_
    last_date: datetime, optional
        Custom checkpoint to check every event after last_date, defaults to None
    handlers: list of Handler, optional
        Event handlers assigned to be called, defaults to [Handler]
    webhook_url: str, optional
        **Discord** webhook url if there is no handlers assigned, defaults to empty string

    Raises
    ------
    Exception
        if no handlers nor webhook_url assigned.
    """

    def __init__(self, token: str, last_date: datetime = None, handlers: List[Handler] = None,
                 webhook_url: str = None, loop=None, emitter: AsyncIOEventEmitter = None,
                 disable_groupfeed: bool = False, disable_mapfeed: bool = False):
        if not handlers:
            self.handlers = []
        else:
            self.handlers = handlers
        self.webhook_url = webhook_url

        self.apitoken = token
        helper.APIKEY = token

        self.last_date = last_date or datetime.utcfromtimestamp(0)
        self.loop = loop or asyncio.get_event_loop()
        self.last_event = None
        self.closed = False
        self.disable_user = disable_groupfeed
        self.disable_map = disable_mapfeed

        self.group_ids = [
            # https://github.com/ppy/osu-web/blob/master/app/Models/UserGroup.php
            4,  # GMT
            7,  # NAT
            16,  # Alumni
            28,  # Full BN
            32  # Probation BN
        ]
        self.last_users = dict()

        for gid in self.group_ids:
            self.last_users[gid] = list()

        self.emitter = emitter or AsyncIOEventEmitter()
        if handlers:
            for handler in handlers:
                handler.register_emitter(self.emitter)

    async def check_map_events(self):
        """Check for map events. |coro|
        """
        events = [event async for event in get_events((1, 1, 1, 1, 1))]
        for i, event in enumerate(events):
            if event.time >= self.last_date:
                beatmap = await event.get_beatmap()

                if event.time == self.last_date:
                    if self.last_event:
                        if beatmap.beatmapset_id == self.last_event.beatmap.beatmapset_id:
                            continue

                if event.time == self.last_date and i + 1 == len(events):
                    self.last_date = event.time + timedelta(seconds=1)
                else:
                    self.last_date = event.time

                self.last_event = event
                if event.event_type not in ["Ranked", "Loved"]:
                    user = await event.source.user()
                    if user['username'] == "BanchoBot":
                        continue

                self.emitter.emit("map_event", event)
                self.emitter.emit(event.event_type.lower(), event)
        
        await asyncio.sleep(5 * 60)

    async def check_role_change(self):
        """Check for role changes. |coro|
        """
        for gid in self.group_ids:
            users = await helper.get_users(gid)

            for user in users:
                if not helper.has_user(user, self.last_users[gid]):
                    self.emitter.emit("group_add", user)
                    self.emitter.emit(user.default_group, user)

            for user in self.last_users[gid]:
                if not helper.has_user(user, users):
                    self.emitter.emit("group_removed", user)
                    self.emitter.emit(user.default_group, user)

            self.last_users[gid] = users
        await asyncio.sleep(15 * 60)

    async def start(self):
        """Well, run the client, what else?! |coro|"""
        if self.disable_map and self.disable_user:
            raise Exception("Cannot disable both map and role check.")
        if not self.handlers:
            if not self.webhook_url:
                raise Exception("Requires Handler or webhook_url")
            self.handlers.append(SimpleHandler(self.webhook_url))

        while not self.closed:
            try:
                event = asyncio.create_task(self.check_map_events()) if not self.disable_map else None
                role = asyncio.create_task(self.check_role_change()) if not self.disable_user else None

                if not self.disable_map:
                    await event
                if not self.disable_user:
                    await role

            except:
                print("An error occured, will keep running anyway.", file=sys.stderr)
                traceback.print_exc()

    def add_handler(self, handler):
        """Adds custom handler to handlers.

        Parameters
        ----------
        handler: object
            The event handler, class must have `parse` function with `event` as argument.
        """
        self.handlers.append(handler)

    def run(self):
        """Run notAiess. This function does not take any parameter.
        """
        def stop():
            self.closed = True
            self.loop.stop()

        try:
            self.loop.add_signal_handler(signal.SIGINT, stop)
            self.loop.add_signal_handler(signal.SIGTERM, stop)
        except NotImplementedError:
            pass

        try:
            self.loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            stop()
            self.loop.close()