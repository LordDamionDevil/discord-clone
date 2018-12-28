"""
discord.pubsub.dispatcher: main dispatcher class
"""
from collections import defaultdict

from logbook import Logger

log = Logger(__name__)


class Dispatcher:
    """Pub/Sub backend dispatcher.
    
    This just declares functions all Dispatcher subclasses
    can implement. This does not mean all Dispatcher
    subclasses have them implemented.
    """

    # the _ parameter is for (self)
    KEY_TYPE = lambda _, x: x
    VAL_TYPE = lambda _, x: x

    def __init__(self, main):
        #: main EventDispatcher
        self.main_dispatcher = main

        #: gateway state storage
        self.sm = main.state_manager

        self.app = main.app

    async def sub(self, _key, _id):
        """Subscribe an element to the channel/key."""
        raise NotImplementedError

    async def unsub(self, _key, _id):
        """Unsubscribe an elemtnt from the channel/key."""
        raise NotImplementedError

    async def dispatch_filter(self, _key, _func, *_args):
        """Selectively dispatch to the list of subscribed users.

        The selection logic is completly arbitraty and up to the
        Pub/Sub backend.
        """
        raise NotImplementedError

    async def dispatch(self, _key, *_args):
        """Dispatch an event to the given channel/key."""
        raise NotImplementedError

    async def reset(self, _key):
        """Reset a key from the backend."""
        raise NotImplementedError

    async def remove(self, _key):
        """Remove a key from the backend.

        The meaning from reset() and remove()
        is different, reset() is to clear all
        subscribers from the given key,
        remove() is to remove the key as well.
        """
        raise NotImplementedError

    async def _dispatch_states(self, states: list, event: str, data) -> int:
        """Dispatch an event to a list of states."""
        res = []

        for state in states:
            try:
                await state.ws.dispatch(event, data)
                res.append(state.session_id)
            except:
                log.exception('error while dispatching')

        return res


class DispatcherWithState(Dispatcher):
    """Pub/Sub backend with a state dictionary.

    This class was made to decrease the amount
    of boilerplate code on Pub/Sub backends
    that have that dictionary.
    """
    def __init__(self, main):
        super().__init__(main)

        #: the default dict is to a set
        #  so we make sure someone calling sub()
        #  twice won't get 2x the events for the
        #  same channel.
        self.state = defaultdict(set)

    async def sub(self, key, identifier):
        self.state[key].add(identifier)

    async def unsub(self, key, identifier):
        self.state[key].discard(identifier)

    async def reset(self, key):
        self.state[key] = set()

    async def remove(self, key):
        try:
            self.state.pop(key)
        except KeyError:
            pass

    async def dispatch(self, key, *args):
        raise NotImplementedError
