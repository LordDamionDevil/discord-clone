from quart import Blueprint, request, current_app as app, jsonify

from logbook import Logger


from discord.blueprints.auth import token_check
from discord.blueprints.checks import channel_check, channel_perm_check
from discord.blueprints.dms import try_dm_state
from discord.errors import MessageNotFound, Forbidden, BadRequest
from discord.enums import MessageType, ChannelType, GUILD_CHANS
from discord.snowflake import get_snowflake
from discord.schemas import validate, MESSAGE_CREATE
from discord.utils import pg_set_json

from discord.embed.sanitizer import fill_embed


log = Logger(__name__)
bp = Blueprint('channel_messages', __name__)


def extract_limit(request_, default: int = 50, max_val: int = 100):
    """Extract a limit kwarg."""
    try:
        limit = int(request_.args.get('limit', default))

        if limit not in range(0, max_val + 1):
            raise ValueError()
    except (TypeError, ValueError):
        raise BadRequest('limit not int')

    return limit


def query_tuple_from_args(args: dict, limit: int) -> tuple:
    """Extract a 2-tuple out of request arguments."""
    before, after = None, None

    if 'around' in request.args:
        average = int(limit / 2)
        around = int(args['around'])

        after = around - average
        before = around + average

    elif 'before' in args:
        before = int(args['before'])
    elif 'after' in args:
        before = int(args['after'])

    return before, after


@bp.route('/<int:channel_id>/messages', methods=['GET'])
async def get_messages(channel_id):
    user_id = await token_check()

    ctype, peer_id = await channel_check(user_id, channel_id)
    await channel_perm_check(user_id, channel_id, 'read_history')

    if ctype == ChannelType.DM:
        # make sure both parties will be subbed
        # to a dm
        await _dm_pre_dispatch(channel_id, user_id)
        await _dm_pre_dispatch(channel_id, peer_id)

    limit = extract_limit(request, 50)

    where_clause = ''
    before, after = query_tuple_from_args(request.args, limit)

    if before:
        where_clause += f'AND id < {before}'

    if after:
        where_clause += f'AND id > {after}'

    message_ids = await app.db.fetch(f"""
    SELECT id
    FROM messages
    WHERE channel_id = $1 {where_clause}
    ORDER BY id DESC
    LIMIT {limit}
    """, channel_id)

    result = []

    for message_id in message_ids:
        msg = await app.storage.get_message(message_id['id'], user_id)

        if msg is None:
            continue

        result.append(msg)

    log.info('Fetched {} messages', len(result))
    return jsonify(result)


@bp.route('/<int:channel_id>/messages/<int:message_id>', methods=['GET'])
async def get_single_message(channel_id, message_id):
    user_id = await token_check()
    await channel_check(user_id, channel_id)
    await channel_perm_check(user_id, channel_id, 'read_history')

    message = await app.storage.get_message(message_id, user_id)

    if not message:
        raise MessageNotFound()

    return jsonify(message)


async def _dm_pre_dispatch(channel_id, peer_id):
    """Do some checks pre-MESSAGE_CREATE so we
    make sure the receiving party will handle everything."""

    # check the other party's dm_channel_state

    dm_state = await app.db.fetchval("""
    SELECT dm_id
    FROM dm_channel_state
    WHERE user_id = $1 AND dm_id = $2
    """, peer_id, channel_id)

    if dm_state:
        # the peer already has the channel
        # opened, so we don't need to do anything
        return

    dm_chan = await app.storage.get_channel(channel_id)

    # dispatch CHANNEL_CREATE so the client knows which
    # channel the future event is about
    await app.dispatcher.dispatch_user(peer_id, 'CHANNEL_CREATE', dm_chan)

    # subscribe the peer to the channel
    await app.dispatcher.sub('channel', channel_id, peer_id)

    # insert it on dm_channel_state so the client
    # is subscribed on the future
    await try_dm_state(peer_id, channel_id)


async def create_message(channel_id: int, actual_guild_id: int,
                         author_id: int, data: dict) -> int:
    message_id = get_snowflake()

    async with app.db.acquire() as conn:
        await pg_set_json(conn)

        await conn.execute(
            """
            INSERT INTO messages (id, channel_id, guild_id, author_id,
                content, tts, mention_everyone, nonce, message_type,
                embeds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            message_id,
            channel_id,
            actual_guild_id,
            author_id,
            data['content'],

            data['tts'],
            data['everyone_mention'],

            data['nonce'],
            MessageType.DEFAULT.value,
            data.get('embeds', [])
        )

    return message_id

async def _guild_text_mentions(payload: dict, guild_id: int,
                               mentions_everyone: bool, mentions_here: bool):
    channel_id = int(payload['channel_id'])

    # calculate the user ids we'll bump the mention count for
    uids = set()

    # first is extracting user mentions
    for mention in payload['mentions']:
        uids.add(int(mention['id']))

    # then role mentions
    for role_mention in payload['mention_roles']:
        role_id = int(role_mention)
        member_ids = await app.storage.get_role_members(role_id)

        for member_id in member_ids:
            uids.add(member_id)

    # at-here only updates the state
    # for the users that have a state
    # in the channel.
    if mentions_here:
        uids = []
        await app.db.execute("""
        UPDATE user_read_state
        SET mention_count = mention_count + 1
        WHERE channel_id = $1
        """, channel_id)

    # at-here updates the read state
    # for all users, including the ones
    # that might not have read permissions
    # to the channel.
    if mentions_everyone:
        uids = []

        member_ids = await app.storage.get_member_ids(guild_id)

        await app.db.executemany("""
        UPDATE user_read_state
        SET mention_count = mention_count + 1
        WHERE channel_id = $1 AND user_id = $2
        """, [(channel_id, uid) for uid in member_ids])

    for user_id in uids:
        await app.db.execute("""
        UPDATE user_read_state
        SET mention_count = mention_count + 1
        WHERE user_id = $1
            AND channel_id = $2
        """, user_id, channel_id)


@bp.route('/<int:channel_id>/messages', methods=['POST'])
async def _create_message(channel_id):
    """Create a message."""
    user_id = await token_check()
    ctype, guild_id = await channel_check(user_id, channel_id)

    actual_guild_id = None

    if ctype in GUILD_CHANS:
        await channel_perm_check(user_id, channel_id, 'send_messages')
        actual_guild_id = guild_id

    j = validate(await request.get_json(), MESSAGE_CREATE)

    # TODO: check connection to the gateway

    can_everyone = await channel_perm_check(
        user_id, channel_id, 'mention_everyone', False
    )

    mentions_everyone = ('@everyone' in j['content']) and can_everyone
    mentions_here = ('@here' in j['content']) and can_everyone

    is_tts = (j.get('tts', False) and
              await channel_perm_check(
                  user_id, channel_id, 'send_tts_messages', False
              ))

    message_id = await create_message(
        channel_id, actual_guild_id, user_id, {
            'content': j['content'],
            'tts': is_tts,
            'nonce': int(j.get('nonce', 0)),
            'everyone_mention': mentions_everyone or mentions_here,

            # fill_embed takes care of filling proxy and width/height
            'embeds': ([await fill_embed(j['embed'])]
                       if 'embed' in j else []),
        })

    payload = await app.storage.get_message(message_id, user_id)

    if ctype == ChannelType.DM:
        # guild id here is the peer's ID.
        await _dm_pre_dispatch(channel_id, user_id)
        await _dm_pre_dispatch(channel_id, guild_id)

    await app.dispatcher.dispatch('channel', channel_id,
                                  'MESSAGE_CREATE', payload)

    # update read state for the author
    await app.db.execute("""
    UPDATE user_read_state
    SET last_message_id = $1
    WHERE channel_id = $2 AND user_id = $3
    """, message_id, channel_id, user_id)

    if ctype == ChannelType.GUILD_TEXT:
        await _guild_text_mentions(payload, guild_id,
                                   mentions_everyone, mentions_here)

    return jsonify(payload)


@bp.route('/<int:channel_id>/messages/<int:message_id>', methods=['PATCH'])
async def edit_message(channel_id, message_id):
    user_id = await token_check()
    _ctype, guild_id = await channel_check(user_id, channel_id)

    author_id = await app.db.fetchval("""
    SELECT author_id FROM messages
    WHERE messages.id = $1
    """, message_id)

    if not author_id == user_id:
        raise Forbidden('You can not edit this message')

    j = await request.get_json()
    updated = 'content' in j or 'embed' in j

    if 'content' in j:
        await app.db.execute("""
        UPDATE messages
        SET content=$1
        WHERE messages.id = $2
        """, j['content'], message_id)

    # TODO: update embed

    # only set new timestamp upon actual update
    if updated:
        await app.db.execute("""
        UPDATE messages
        SET edited_at = (now() at time zone 'utc')
        WHERE id = $1
        """, message_id)

    message = await app.storage.get_message(message_id, user_id)

    # only dispatch MESSAGE_UPDATE if any update
    # actually happened
    if updated:
        await app.dispatcher.dispatch('channel', channel_id,
                                      'MESSAGE_UPDATE', message)

    return jsonify(message)


@bp.route('/<int:channel_id>/messages/<int:message_id>', methods=['DELETE'])
async def delete_message(channel_id, message_id):
    user_id = await token_check()
    _ctype, guild_id = await channel_check(user_id, channel_id)

    author_id = await app.db.fetchval("""
    SELECT author_id FROM messages
    WHERE messages.id = $1
    """, message_id)

    by_perm = await channel_perm_check(
        user_id, channel_id, 'manage_messages', False
    )

    by_ownership = author_id == user_id

    can_delete = by_perm or by_ownership
    if not can_delete:
        raise Forbidden('You can not delete this message')

    await app.db.execute("""
    DELETE FROM messages
    WHERE messages.id = $1
    """, message_id)

    await app.dispatcher.dispatch(
        'channel', channel_id,
        'MESSAGE_DELETE', {
            'id': str(message_id),
            'channel_id': str(channel_id),

            # for lazy guilds
            'guild_id': str(guild_id),
        })

    return '', 204
