# Automatically reload program when code is changed
# borrowed from Django (https://www.djangoproject.com/)

import os, sys, time, signal, traceback
try:
    import termios
except ImportError:
    termios = None
try:
    import thread as thread
except ImportError:
    import dummy_thread as thread


_win = (sys.platform == "win32")
# get files
class FileDetector(object):
    def __init__(self):
        self._error_files = []
        self.filenames = []
        self.mtimes = {}

    def detect_all_files(self):
        """ Get all involved module files.  """
        def trans_filenames(filenames):
            for i,filename in enumerate(filenames):
                if not filename: del filenames[i]
                if filename.endswith(".pyc") or \
                        filename.endswith("pyo"):
                    filenames[i] = filename[:-1]
                if filename.endswith("$py.class"):
                    filenames[i] = filename[:-9] + ".py"
                if not os.path.exists(filename):
                    del filenames[i]
                    continue
        for m in sys.modules.values():
            try:
                self.filenames.append(m.__file__)
            except AttributeError:
                pass
        trans_filenames(self.filenames)
        trans_filenames(self._error_files)

    def change_detected(self):
        for filename in self.filenames + self._error_files:
            stat = os.stat(filename)
            mtime = stat.st_mtime - stat.st_ctime if _win else os.stat(filename)
            if filename not in self.mtimes:
                self.mtimes[filename] = mtime
                continue
            # file is changed
            if mtime != self.mtimes[filename]:
                self.mtimes.clear()
                try:
                    del self._error_files[
                            self._error_files.index(filename) ]
                except ValueError:
                    pass
                return True
        return False

    def check_errors(self, fn):
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except (ImportError, IndentationError, NameError, SyntaxError,
                    TypeError, AttributeError):
                _type, _value, _traceback = sys.exc_info()
                if getattr(_value, 'filename', None) is None:
                    # get the filename from last item in the stack
                    filename = traceback.extract_tb(_traceback)[-1][0]
                else:
                    filename = _value.filename

                if filename not in self._error_files:
                    self._error_files.append(filename)
                raise
        return wrapper
    

file_detector = FileDetector()


class Reloader(object):
    RUN_RELOADER = True

    def ensure_echo_on(self):
        if termios:
            fd = sys.stdin
            if fd.isatty():
                attr_list = termios.tcgetattr(fd)
                if not attr_list[3] & termios.ECHO:
                    attr_list[3] |= termios.ECHO
                    if hasattr(signal, 'SIGTTOU'):
                        old_handler = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
                    else:
                        old_handler = None
                    termios.tcsetattr(fd, termios.TCSANOW, attr_list)
                    if old_handler is not None:
                        signal.signal(signal.SIGTTOU, old_handler)

    def reloader_thread(self):
        self.ensure_echo_on()
        while self.RUN_RELOADER:
            file_detector.detect_all_files()
            if file_detector.change_detected():
                sys.exit(3) # force reload
            time.sleep(1)

    def restart_with_reloader(self):
        while True:
            args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions] + sys.argv
            if sys.platform == "win32":
                args = ['"%s"' % arg for arg in args]
            new_environ = os.environ.copy()
            new_environ["RUN_MAIN"] = 'true'
            exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
            if exit_code != 3:
                return exit_code

    def python_reloader(self, main_func, *args, **kwargs):
        print '%s python reload thread' % str(time.ctime())
        if os.environ.get("RUN_MAIN") == "true":
            thread.start_new_thread(main_func, args, kwargs)
            try:
                self.reloader_thread()
            except KeyboardInterrupt:
                pass
        else:
            try:
                exit_code = self.restart_with_reloader()
                if exit_code < 0:
                    os.kill(os.getpid(), -exit_code)
                else:
                    sys.exit(exit_code)
            except KeyboardInterrupt:
                pass
            
    def jython_reloader(self, main_func, *args, **kwargs):
        print '%s jython reload thread' % str(time.ctime())
        from _systemrestart import SystemRestart
        thread.start_new_thread(main_func, args)
        while True:
            if file_detector.change_detected():
                raise SystemRestart
            time.sleep(1)

reloader = Reloader()

def main(main_func, *args, **kwargs):
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    if sys.platform.startswith('java'):
        _reloader = reloader.jython_reloader
    else:
        _reloader = reloader.python_reloader
    wrapped_main_func = file_detector.check_errors(main_func)
    _reloader(wrapped_main_func, *args, **kwargs)
