from quart import Blueprint, request, current_app as app, jsonify

from discord.blueprints.auth import token_check
from discord.blueprints.checks import guild_perm_check

from discord.schemas import validate, GUILD_PRUNE

bp = Blueprint('guild_moderation', __name__)


async def remove_member(guild_id: int, member_id: int):
    """Do common tasks related to deleting a member from the guild,
    such as dispatching GUILD_DELETE and GUILD_MEMBER_REMOVE."""

    await app.db.execute("""
    DELETE FROM members
    WHERE guild_id = $1 AND user_id = $2
    """, guild_id, member_id)

    await app.dispatcher.dispatch_user_guild(
        member_id, guild_id, 'GUILD_DELETE', {
            'guild_id': str(guild_id),
            'unavailable': False,
        })

    await app.dispatcher.unsub('guild', guild_id, member_id)

    await app.dispatcher.dispatch(
        'lazy_guild', guild_id, 'remove_member', member_id)

    await app.dispatcher.dispatch_guild(guild_id, 'GUILD_MEMBER_REMOVE', {
        'guild_id': str(guild_id),
        'user': await app.storage.get_user(member_id),
    })


async def remove_member_multi(guild_id: int, members: list):
    """Remove multiple members."""
    for member_id in members:
        await remove_member(guild_id, member_id)


@bp.route('/<int:guild_id>/members/<int:member_id>', methods=['DELETE'])
async def kick_guild_member(guild_id, member_id):
    """Remove a member from a guild."""
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'kick_members')
    await remove_member(guild_id, member_id)
    return '', 204


@bp.route('/<int:guild_id>/bans', methods=['GET'])
async def get_bans(guild_id):
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'ban_members')

    bans = await app.db.fetch("""
    SELECT user_id, reason
    FROM bans
    WHERE bans.guild_id = $1
    """, guild_id)

    res = []

    for ban in bans:
        res.append({
            'reason': ban['reason'],
            'user': await app.storage.get_user(ban['user_id'])
        })

    return jsonify(res)


@bp.route('/<int:guild_id>/bans/<int:member_id>', methods=['PUT'])
async def create_ban(guild_id, member_id):
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'ban_members')

    j = await request.get_json()

    await app.db.execute("""
    INSERT INTO bans (guild_id, user_id, reason)
    VALUES ($1, $2, $3)
    """, guild_id, member_id, j.get('reason', ''))

    await remove_member(guild_id, member_id)

    await app.dispatcher.dispatch_guild(guild_id, 'GUILD_BAN_ADD', {
        'guild_id': str(guild_id),
        'user': await app.storage.get_user(member_id)
    })

    return '', 204


@bp.route('/<int:guild_id>/bans/<int:banned_id>', methods=['DELETE'])
async def remove_ban(guild_id, banned_id):
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'ban_members')

    res = await app.db.execute("""
    DELETE FROM bans
    WHERE guild_id = $1 AND user_id = $@
    """, guild_id, banned_id)

    # we don't really need to dispatch GUILD_BAN_REMOVE
    # when no bans were actually removed.
    if res == 'DELETE 0':
        return '', 204

    await app.dispatcher.dispatch_guild(guild_id, 'GUILD_BAN_REMOVE', {
        'guild_id': str(guild_id),
        'user': await app.storage.get_user(banned_id)
    })

    return '', 204


async def get_prune(guild_id: int, days: int) -> list:
    """Get all members in a guild that:

     - did not login in ``days`` days.
     - don't have any roles.
    """
    # a good solution would be in pure sql.
    member_ids = await app.db.fetch(f"""
    SELECT id
    FROM users
    JOIN members
    ON members.guild_id = $1 AND members.user_id = users.id
    WHERE users.last_session < (now() - (interval '{days} days'))
    """, guild_id)

    member_ids = [r['id'] for r in member_ids]
    members = []

    for member_id in member_ids:
        role_count = await app.db.fetchval("""
        SELECT COUNT(*)
        FROM member_roles
        WHERE guild_id = $1 AND user_id = $2
        """, guild_id, member_id)

        if role_count == 0:
            members.append(member_id)

    return members


@bp.route('/<int:guild_id>/prune', methods=['GET'])
async def get_guild_prune_count(guild_id):
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'kick_members')

    j = validate(await request.get_json(), GUILD_PRUNE)
    days = j['days']
    member_ids = await get_prune(guild_id, days)

    return jsonify({
        'pruned': len(member_ids),
    })


@bp.route('/<int:guild_id>/prune', methods=['POST'])
async def begin_guild_prune(guild_id):
    user_id = await token_check()

    await guild_perm_check(user_id, guild_id, 'kick_members')

    j = validate(await request.get_json(), GUILD_PRUNE)
    days = j['days']
    member_ids = await get_prune(guild_id, days)

    app.loop.create_task(remove_member_multi(guild_id, member_ids))

    return jsonify({
        'pruned': len(member_ids)
    })
