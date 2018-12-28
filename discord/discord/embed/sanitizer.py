"""
discord.embed.sanitizer
    sanitize embeds by giving common values
    such as type: rich
"""
from typing import Dict, Any

from logbook import Logger
from quart import current_app as app

log = Logger(__name__)
Embed = Dict[str, Any]


def sanitize_embed(embed: Embed) -> Embed:
    """Sanitize an embed object.

    This is non-complex sanitization as it doesn't
    need the app object.
    """
    return {**embed, **{
        'type': 'rich'
    }}


def path_exists(embed: Embed, components: str):
    """Tell if a given path exists in an embed (or any dictionary).

    The components string is formatted like this:
        key1.key2.key3.key4. <...> .keyN

    with each key going deeper and deeper into the embed.
    """

    # get the list of components given
    if isinstance(components, str):
        components = components.split('.')
    else:
        components = list(components)

    # if there are no components, we reached the end of recursion
    # and can return true
    if not components:
        return True

    # extract current component
    current = components[0]

    # if it exists, then we go down a level inside the dict
    # (via recursion)
    if current in embed:
        return path_exists(embed[current], components[1:])

    # if it doesn't exist, return False
    return False


def proxify(url) -> str:
    """Return a mediaproxy url for the given EmbedURL."""

    md_base_url = app.config['MEDIA_PROXY']
    parsed = url.parsed
    proto = 'https' if app.config['IS_SSL'] else 'http'

    return (
        # base mediaproxy url
        f'{proto}://{md_base_url}/img/'
        f'{parsed.scheme}/{parsed.netloc}{parsed.path}'
    )


async def fetch_metadata(url) -> dict:
    """Fetch metadata for a url."""
    parsed = url.parsed

    md_path = f'{parsed.scheme}/{parsed.netloc}{parsed.path}'

    md_base_url = app.config['MEDIA_PROXY']
    proto = 'https' if app.config['IS_SSL'] else 'http'

    request_url = f'{proto}://{md_base_url}/meta/{md_path}'

    async with app.session.get(request_url) as resp:
        if resp.status != 200:
            return

        return await resp.json()


async def fill_embed(embed: Embed) -> Embed:
    """Fill an embed with more information."""
    embed = sanitize_embed(embed)

    if path_exists(embed, 'footer.icon_url'):
        embed['footer']['proxy_icon_url'] = \
            proxify(embed['footer']['icon_url'])

    if path_exists(embed, 'author.icon_url'):
        embed['author']['proxy_icon_url'] = \
            proxify(embed['author']['icon_url'])

    if path_exists(embed, 'image.url'):
        image_url = embed['image']['url']

        meta = await fetch_metadata(image_url)
        embed['image']['proxy_url'] = proxify(image_url)

        if meta and meta['image']:
            embed['image']['width'] = meta['width']
            embed['image']['height'] = meta['height']

    return embed
