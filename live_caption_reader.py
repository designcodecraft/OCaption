"""
A small helper that reads the Windows Live Captions UI using pywinauto (UIA backend).
It periodically attempts to locate a window/control that contains the captions and returns
its text content.

Usage:
    reader = LiveCaptionReader()
    reader.start()
    # then poll reader.latest_text or subscribe to callback
    reader.stop()

This is best-effort — depending on Windows version and Live Captions implementation the
control names or structure may differ. If not found, the reader will keep trying.
"""
from threading import Thread, Event
import time
import re

try:
    from pywinauto import Desktop
except Exception:
    Desktop = None

class LiveCaptionReader:
    def __init__(self, poll_interval=0.5):
        self.poll_interval = poll_interval
        self._stop_event = Event()
        self._thread = None
        self.latest_text = ""
        self.on_change = None  # optional callback(text)

    def _find_caption_control(self):
        if Desktop is None:
            return None

        try:
            d = Desktop(backend="uia")
            # Attempt a few heuristics to find the Live Captions window or text control
            # 1) window with title containing 'Live captions' (English) - case insensitive
            try:
                win = d.window(title_re='(?i).*Live captions.*')
                if win.exists():
                    # find text descendant - usually the caption display control
                    txt = win.descendants(control_type='Text')
                    if txt:
                        return txt[0]
            except Exception:
                pass

            # 2) Try alternate window titles (localized versions)
            for pattern in ['(?i).*caption.*', '(?i).*subtitle.*']:
                try:
                    win = d.window(title_re=pattern)
                    if win.exists():
                        # Check if this window has the typical Live Captions structure
                        txt = win.descendants(control_type='Text')
                        if txt and len(txt) > 0:
                            # Verify it's likely the caption window (has single large text control)
                            try:
                                test_text = txt[0].window_text()
                                if test_text or len(txt) == 1:  # Either has text or is the only text control
                                    return txt[0]
                            except Exception:
                                pass
                except Exception:
                    pass

            # 3) Last resort: search for windows with specific class name patterns (Win11 Live Captions)
            try:
                all_windows = d.windows()
                for w in all_windows:
                    try:
                        if not w.is_visible():
                            continue
                        # Check window properties that indicate Live Captions
                        try:
                            win_title = w.window_text()
                            if win_title and ('caption' in win_title.lower() or 'subtitle' in win_title.lower()):
                                texts = w.descendants(control_type='Text')
                                if texts:
                                    return texts[0]
                        except Exception:
                            pass
                    except Exception:
                        continue
            except Exception:
                pass
        except Exception:
            return None

        return None

    def _poll_loop(self):
        ctrl = None
        refresh_counter = 0
        while not self._stop_event.is_set():
            try:
                # Force refresh every 2 iterations to pick up newly opened Live Captions quickly
                if ctrl is None or refresh_counter >= 2:
                    ctrl = self._find_caption_control()
                    refresh_counter = 0
                
                refresh_counter += 1
                
                if ctrl is not None:
                    try:
                        text = ctrl.window_text()
                    except Exception:
                        # control may have gone stale
                        ctrl = None
                        refresh_counter = 10  # Force immediate refresh
                        text = ""

                    if text and text != self.latest_text:
                        # Keep the full text for change detection
                        full_text = text
                        self.latest_text = full_text

                        # Extract the most recent segment (last non-empty line)
                        parts = [p.strip() for p in re.split(r'\r?\n', full_text) if p.strip()]
                        if parts:
                            tail = parts[-1]
                        else:
                            tail = full_text.strip()

                        # If tail is very long, trim to the last ~200 chars at a word boundary
                        if len(tail) > 200:
                            tail = tail[-200:]
                            if ' ' in tail:
                                tail = tail[tail.find(' ')+1:]

                        # Avoid sending identical tail repeatedly
                        last_sent = getattr(self, '_last_sent', None)
                        if tail and tail != last_sent:
                            self._last_sent = tail
                            if self.on_change:
                                try:
                                    self.on_change(tail)
                                except Exception:
                                    pass
                time.sleep(self.poll_interval)
            except Exception:
                time.sleep(self.poll_interval)

    def start(self):
        if Desktop is None:
            raise RuntimeError('pywinauto is not available in the environment')
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def get_current_text(self, timeout: float = 2.0, poll: float = 0.15) -> str:
        """Try to locate the captions control and return its current full text.

        This actively searches (same heuristics as the poll loop) for up to
        `timeout` seconds and returns the control text if found, otherwise
        an empty string.
        """
        if Desktop is None:
            return ""

        end = time.time() + max(0.0, float(timeout))
        while time.time() < end:
            try:
                ctrl = self._find_caption_control()
                if ctrl is not None:
                    try:
                        text = ctrl.window_text()
                        if text:
                            return text
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(poll)
        return ""

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None


if __name__ == '__main__':
    # Quick local test when run directly
    r = LiveCaptionReader()
    def cb(t):
        print('Caption:', t)
    r.on_change = cb
    try:
        r.start()
        print('Started live caption reader. Press Ctrl+C to stop.')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        r.stop()
        print('Stopped')
