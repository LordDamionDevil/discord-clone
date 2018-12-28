class DiscordError(Exception):
    status_code = 500

    @property
    def message(self):
        try:
            return self.args[0]
        except IndexError:
            return repr(self)

    @property
    def json(self):
        return self.args[1]


class BadRequest(DiscordError):
    status_code = 400


class Unauthorized(DiscordError):
    status_code = 401


class Forbidden(DiscordError):
    status_code = 403


class NotFound(DiscordError):
    status_code = 404


class GuildNotFound(NotFound):
    error_code = 10004


class ChannelNotFound(NotFound):
    error_code = 10003


class MessageNotFound(NotFound):
    error_code = 10008


class Ratelimited(DiscordError):
    status_code = 429


class MissingPermissions(Forbidden):
    error_code = 50013


class WebsocketClose(Exception):
    @property
    def code(self):
        return self.args[0]

    @property
    def reason(self):
        return self.args[1]
