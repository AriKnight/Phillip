There are lots of helper functions in Phillip as it tries to have as little dependencies as possible.
This will help you access requests data from osu! and process them.

## osu! API

In this section we will only bring functions to help you with osu! API. (v1, obviously.)

---

::: phillip.osu.APIClient
    :members:

!!! info
    `phillip.helper.get_beatmap_api` is a shorthand of `phillip.helper.get_api('get_beatmaps', **kwargs)`.
    Same goes with `get_user`.

## osu!web

In this section, we will scrape the site in order to get data from osu!

!!! warning
    A throttler is auto initiated to rate limit your request to **2 requests/minute** 
    in order to avoid getting banned. You may change this but in general this is **highly discouraged**.

---

::: phillip.osu.WebClient
    :members:


## Discord Webhook

To help you generate webhooks, I have made an Aiess-styled webhook generator for events.

::: phillip.helper.gen_embed
    :docstring:

