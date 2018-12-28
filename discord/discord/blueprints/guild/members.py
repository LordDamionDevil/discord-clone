from quart import Blueprint, request, current_app as app, jsonify

from discord.blueprints.auth import token_check
from discord.errors import BadRequest

from discord.schemas import (
    validate, MEMBER_UPDATE
)

from discord.blueprints.checks import (
    guild_check, guild_owner_check, guild_perm_check
)

bp = Blueprint('guild_members', __name__)


@bp.route('/<int:guild_id>/members/<int:member_id>', methods=['GET'])
async def get_guild_member(guild_id, member_id):
    """Get a member's information in a guild."""
    user_id = await token_check()
    await guild_check(user_id, guild_id)
    member = await app.storage.get_single_member(guild_id, member_id)
    return jsonify(member)


@bp.route('/<int:guild_id>/members', methods=['GET'])
async def get_members(guild_id):
    """Get members inside a guild."""
    user_id = await token_check()
    await guild_check(user_id, guild_id)

    j = await request.get_json()

    limit, after = int(j.get('limit', 1)), j.get('after', 0)

    if limit < 1 or limit > 1000:
        raise BadRequest('limit not in 1-1000 range')

    user_ids = await app.db.fetch(f"""
    SELECT user_id
    WHERE guild_id = $1, user_id > $2
    LIMIT {limit}
    ORDER BY user_id ASC
    """, guild_id, after)

    user_ids = [r[0] for r in user_ids]
    members = await app.storage.get_member_multi(guild_id, user_ids)
    return jsonify(members)


async def _update_member_roles(guild_id: int, member_id: int,
                               wanted_roles: list):
    """Update the roles a member has."""

    # first, fetch all current roles
    roles = await app.db.fetch("""
    SELECT role_id from member_roles
    WHERE guild_id = $1 AND user_id = $2
    """, guild_id, member_id)

    roles = [r['role_id'] for r in roles]

    roles = set(roles)
    wanted_roles = set(wanted_roles)

    # first, we need to find all added roles:
    # roles that are on wanted_roles but
    # not on roles
    added_roles = wanted_roles - roles

    # and then the removed roles
    # which are roles in roles, but not
    # in wanted_roles
    removed_roles = roles - wanted_roles

    conn = await app.db.acquire()

    async with conn.transaction():
        # add roles
        await app.db.executemany("""
        INSERT INTO member_roles (user_id, guild_id, role_id)
        VALUES ($1, $2, $3)
        """, [(member_id, guild_id, role_id)
              for role_id in added_roles])

        # remove roles
        await app.db.executemany("""
        DELETE FROM member_roles
        WHERE
            user_id = $1
        AND guild_id = $2
        AND role_id = $3
        """, [(member_id, guild_id, role_id)
              for role_id in removed_roles])

    await app.db.release(conn)


@bp.route('/<int:guild_id>/members/<int:member_id>', methods=['PATCH'])
async def modify_guild_member(guild_id, member_id):
    """Modify a members' information in a guild."""
    user_id = await token_check()
    await guild_owner_check(user_id, guild_id)

    j = validate(await request.get_json(), MEMBER_UPDATE)
    nick_flag = False

    if 'nick' in j:
        await guild_perm_check(user_id, guild_id, 'manage_nicknames')

        nick = j['nick'] or None

        await app.db.execute("""
        UPDATE members
        SET nickname = $1
        WHERE user_id = $2 AND guild_id = $3
        """, nick, member_id, guild_id)

        nick_flag = True

    if 'mute' in j:
        await guild_perm_check(user_id, guild_id, 'mute_members')

        await app.db.execute("""
        UPDATE members
        SET muted = $1
        WHERE user_id = $2 AND guild_id = $3
        """, j['mute'], member_id, guild_id)

    if 'deaf' in j:
        await guild_perm_check(user_id, guild_id, 'deafen_members')

        await app.db.execute("""
        UPDATE members
        SET deafened = $1
        WHERE user_id = $2 AND guild_id = $3
        """, j['deaf'], member_id, guild_id)

    if 'channel_id' in j:
        # TODO: check MOVE_MEMBERS and CONNECT to the channel
        # TODO: change the member's voice channel
        pass

    if 'roles' in j:
        await guild_perm_check(user_id, guild_id, 'manage_roles')
        await _update_member_roles(guild_id, member_id, j['roles'])

    member = await app.storage.get_member_data_one(guild_id, member_id)
    member.pop('joined_at')

    # call pres_update for role and nick changes.
    partial = {
        'roles': member['roles']
    }

    if nick_flag:
        partial['nick'] = j['nick']

    await app.dispatcher.dispatch(
        'lazy_guild', guild_id, 'pres_update', user_id, partial)

    await app.dispatcher.dispatch_guild(guild_id, 'GUILD_MEMBER_UPDATE', {**{
        'guild_id': str(guild_id)
    }, **member})

    return '', 204


@bp.route('/<int:guild_id>/members/@me/nick', methods=['PATCH'])
async def update_nickname(guild_id):
    """Update a member's nickname in a guild."""
    user_id = await token_check()
    await guild_check(user_id, guild_id)

    j = validate(await request.get_json(), {
        'nick': {'type': 'nickname'}
    })

    nick = j['nick'] or None

    await app.db.execute("""
    UPDATE members
    SET nickname = $1
    WHERE user_id = $2 AND guild_id = $3
    """, nick, user_id, guild_id)

    member = await app.storage.get_member_data_one(guild_id, user_id)
    member.pop('joined_at')

    # call pres_update for nick changes, etc.
    await app.dispatcher.dispatch(
        'lazy_guild', guild_id, 'pres_update', user_id, {
            'nick': j['nick']
        })

    await app.dispatcher.dispatch_guild(guild_id, 'GUILD_MEMBER_UPDATE', {**{
        'guild_id': str(guild_id)
    }, **member})

    return j['nick']
