from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from phillip.osu.classes.api import Beatmap as ApiBeatmap
from phillip.osu.classes.web import Beatmap as WebBeatmap
from phillip.osu.classes.web import Discussion


class EventBase(ABC):
    """An Abstract Class (ABC) representing base osu! beatmapset event.
    """

    def __init__(self, js: dict, next_event: dict = None, app=None):
        self.app = app
        self.js = js
        self.next_event = next_event
        self._beatmap = None

    async def get_beatmap(self):
        if not self._beatmap:
            self._beatmap = await self.app.api.get_beatmaps(s=self.beatmapset.id)
        return self._beatmap

    @property
    def creator(self) -> str:
        """Mapper of beatmap."""
        return self.beatmapset.creator

    @property
    def artist(self) -> str:
        """Beatmap's artist."""
        return self.beatmapset.artist

    @property
    def title(self) -> str:
        """Beatmap's title."""
        return self.beatmapset.title

    @property
    def map_cover(self) -> str:
        """URL to map's cover image."""
        return self.beatmapset.covers["list@2x"]

    @property
    def user_id(self) -> int:
        """The user that causes this event to occur."""
        return self.js["user_id"]

    @property
    def time(self) -> datetime:
        """A `datetime` object representing the time where the event happened."""
        dt = self.js["created_at"]
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S+00:00")

    @abstractmethod
    def event_type(self):
        """Event that happened on the beatmap (bubbled, qualified, etc.)"""
        pass

    @property
    def event_source_url(self) -> str:
        """URL to event cause."""
        return f"https://osu.ppy.sh/s/{self.beatmapset.id}"

    @property
    def gamemodes(self) -> List[str]:
        """Game modes inside the beatmapset."""
        if not self.api_beatmap:
            raise Exception("Beatmap data not initialized.")

        mode_num = {"0": "osu", "1": "taiko", "2": "catch", "3": "mania"}
        modes = []
        for diff in self.api_beatmap:
            if mode_num[diff.mode] not in modes:
                modes.append(mode_num[diff.mode])
        return modes

    @property
    def api_beatmap(self) -> ApiBeatmap:
        """First difficulty of the beatmap, usually the first entry from osu! API."""
        return self._beatmap

    @property
    def beatmapset(self) -> WebBeatmap:
        """Array of difficulties inside the beatmap."""
        return WebBeatmap(self.js["beatmapset"])

    @property
    def discussion(self) -> Discussion:
        js_obj = self.js.get("discussion")
        if not js_obj:
            return None
        return Discussion(js_obj)
