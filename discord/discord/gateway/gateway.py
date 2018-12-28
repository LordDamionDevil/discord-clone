import urllib.parse
from .websocket import GatewayWebsocket


async def websocket_handler(app, ws, url):
    """Main websocket handler, checks query arguments
    when connecting to the gateway and spawns a
    GatewayWebsocket instance for the connection."""
    args = urllib.parse.parse_qs(
        urllib.parse.urlparse(url).query
    )

    # pull a dict.get but in a really bad way.
    try:
        gw_version = args['v'][0]
    except (KeyError, IndexError):
        gw_version = '6'

    try:
        gw_encoding = args['encoding'][0]
    except (KeyError, IndexError):
        gw_encoding = 'json'

    if gw_version not in ('6', '7'):
        return await ws.close(1000, 'Invalid gateway version')

    if gw_encoding not in ('json', 'etf'):
        return await ws.close(1000, 'Invalid gateway encoding')

    try:
        gw_compress = args['compress'][0]
    except (KeyError, IndexError):
        gw_compress = None

    if gw_compress and gw_compress not in ('zlib-stream',):
        return await ws.close(1000, 'Invalid gateway compress')

    gws = GatewayWebsocket(ws, app, v=gw_version,
                           encoding=gw_encoding, compress=gw_compress)
    await gws.run()
