# Session module.
# Borrowed from web.py project (http://webpy.org/)

import re
import os, time, datetime, random, base64
from copy import deepcopy
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle

import swinf
from swinf import HTTPError
from swinf.utils import Storage, ThreadDict
sha1 = hashlib.sha1

__all__ = [
    "SessionExpired", "session_config", 
    "session_id_opt", "Session",
    "StoreAdapter", "DiskStore", "ShelfStore",
]

class SessionExpired(HTTPError):
    def __init__(self, message):
        HTTPError.__init__(self, '200', message)


# empty config for session
# user can deep_copy it and get specific config
# should update the settings first or the cookie will
# not work
session_config = Storage({
    'cookie_name': 'session_id',
    'cookie_domain': None,
    'cookie_path' : None,
    'timeout': 60, #24 * 60 * 60, # 24 hours in seconds
    'ignore_expiry': True,
    'ignore_change_ip': True,
    'secret_key': 'fLjUfxqXtfNoIldA0A0J',
    'expired_message': 'Session expired',
    'httponly': True,
    'secure': False
})


class SessionIdOpt(object):
    """Operator of session if."""
    @staticmethod
    def generate(secret_key, store):
        """Generate an unique new random id for session"""
        while True:
            rand = os.urandom(16)
            now = time.time()
            secret_key = secret_key
            session_id = sha1("%s%s%s%s" %(rand, now, swinf.request.remote_addr, secret_key))
            session_id = session_id.hexdigest()
            if session_id not in store:
                break
        return session_id

    @staticmethod
    def validate(session_id):
        rx = re.compile('^[0-9a-fA-F]+$')
        return rx.match(session_id)

session_id_opt = SessionIdOpt()


class Session(swinf.HandlerHookAdapter):
    """
    Session management

    work as a handler hook, and will insert process into WSGIHandler process.
    """
    def __init__(self, store, hook=None, initializer=None, config=session_config):
        self.store = store
        self.initializer = initializer
        self.config = Storage(config)
        self.data = ThreadDict()
        self._last_cleanup_time = 0

        # signals
        # If the brower set valid sessid_id then 
        # the session_id will not be changed
        self.__valid_session_id = False
        self.__data_changed = False

        if hook != None: 
            hook.add_processor('session_processor', self)
        self.__getitem__ = self.data.__getitem__
        self.__setitem__ = self.data.__setitem__
        self.__delitem__ = self.data.__delitem__
        self.update = self.data.update

    def load(self):
        """Load the session from the store, by the id from cookie"""
        cookie_name = self.config.cookie_name
        self.session_id = swinf.request.COOKIES.get(cookie_name)
        self.ip = swinf.request.remote_addr
        if self.session_id and not \
                session_id_opt.validate(self.session_id):
            self.session_id = None
        self.check_expiry()
        if self.session_id:
            self._session_id_valid()
            # self.data get data from d
            d = self.store[self.session_id]
            self.update(d)
            # TODO self.validate_ip()
        # create a new session_id
        else:
            self._session_id_invalid()
            self.session_id = session_id_opt.generate(\
                    self.config.secret_key, self.store)
            if self.initializer:
                if isinstance(self.initializer, dict):
                    self.update(deepcopy(self.initializer))
                

    def _cleanup(self):
        """Periodically cleanup the stored sessions."""
        current_time = time.time()
        timeout = self.config.timeout
        if current_time - self._last_cleanup_time > timeout:
            self.store.cleanup(timeout)
            self._last_cleanup_time = current_time

    def check_expiry(self):
        """ Check if the session_id is expiried.

        Self.store contains all the valid sessions, and will automatically be cleaned periodically. 
        If a session is out of time, then store will delete it.  """
        if self.session_id and self.session_id not in self.store:
            self._session_id_invalid()
            if self.config.ignore_expiry:
                self.session_id = None
            else:
                return self.expired()

    def _validate_ip(self):
        """ check for change of IP"""
        if self.session_id and self.get('ip', None) \
                != swinf.request.remote_addr:
            if not self.config.ignore_change_ip:
               return self.expired() 

    def expired(self):
        """Called when an expired session is atime"""
        self._killed = True
        self.save()
        raise SessionExpired(self.config.expired_message)

    def _setcookie(self, session_id, expires='', **kwargs):
        """ Add cookies to response """
        cookie_name = self.config.cookie_name
        cookie_setting = {
            'domain' : self.config.cookie_domain,
            'path' : self.config.cookie_path,
            'httponly' : self.config.httponly,
            'secure' : self.config.secure, }
        for key, value in cookie_setting.items():
            if value is None or value is False:
                del cookie_setting[key]
        swinf.response.set_cookie(cookie_name,  session_id, **cookie_setting)
 
    def kill(self):
        """Kill the session, make it no longer available"""
        del self.store[self.session_id]
        self._killed = True

    def save(self):
        if not getattr(self, '_killed', False):
            if not self.__valid_session_id:
                self._setcookie(self.session_id)
            self.store[self.session_id] = dict(self.data)
        else:
            self._setcookie(self.session_id)

    def hook_start(self):
        """Impliment HandlerHookAdapter.hook_start """
        self._cleanup()
        self.load()

    def hook_end(self):
        """Impliment HandlerHookAdapter.hook_end """
        self.save()

    def __contains__(self, name):
        return name in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def  __delitem__(self, key):
        del self.data[key]

    def _session_id_valid(self):
        self.__valid_session_id = True

    def _session_id_invalid(self):
        self.__valid_session_id = False

    def _data_changed(self, sig=None):
        if sig is not None:
            self.__data_changed = True
        else:
            return self.__data_changed

from swinf.core.middleware import SessionStoreAdapter


class DiskStore(SessionStoreAdapter):
    """
    Store for saving a session on disk.
    """
    def __init__(self, root):
        # if the storage root doesn't exists, create it.
        if not os.path.exists(root):
            os.makedirs( 
                os.path.abspath(root))
        self.root = root

    def _get_path(self, key):
        if os.path.sep in key: 
            raise ValueError, "Bad key: %s" % repr(key)
        return os.path.join(self.root, key)
    
    def __contains__(self, key):
        path = self._get_path(key)
        return os.path.exists(path)

    def __getitem__(self, key):
        path = self._get_path(key)
        if os.path.exists(path): 
            pickled = open(path).read()
            return self.decode(pickled)
        else:
            raise KeyError, key

    def __setitem__(self, key, value):
        path = self._get_path(key)
        pickled = self.encode(value)    
        try:
            f = open(path, 'w')
            try:
                f.write(pickled)
            finally: 
                f.close()
        except IOError:
            pass

    def __delitem__(self, key):
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)
    
    def cleanup(self, timeout):
        now = time.time()
        for f in os.listdir(self.root):
            path = self._get_path(f)
            atime = os.stat(path).st_atime
            if now - atime > timeout :
                os.remove(path)


class ShelfStore:
    """Store for saving session using `shelve` module.

        import shelve
        store = ShelfStore(shelve.open('session.shelf'))

    XXX: is shelve thread-safe?
    """
    def __init__(self, shelf):
        self.shelf = shelf

    def __contains__(self, key):
        return key in self.shelf

    def __getitem__(self, key):
        atime, v = self.shelf[key]
        self[key] = v # update atime
        return v

    def __setitem__(self, key, value):
        self.shelf[key] = time.time(), value
        
    def __delitem__(self, key):
        try:
            del self.shelf[key]
        except KeyError:
            pass

    def cleanup(self, timeout):
        now = time.time()
        for k in self.shelf.keys():
            atime, v = self.shelf[k]
            if now - atime > timeout :
                del self[k]
