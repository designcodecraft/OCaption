import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import os
import sys
from app_meta import load as load_meta
try:
    from live_caption_reader import LiveCaptionReader
except Exception:
    LiveCaptionReader = None
import re
import ctypes
import time

class CaptionerApp:
    def __init__(self, root):
        self.root = root
        # Determine base directory (supports PyInstaller one-file exe)
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(__file__)
        except Exception:
            base_dir = os.path.dirname(__file__)
        self._base_dir = base_dir
        # Ensure transcript folder exists
        try:
            self._transcript_dir = os.path.join(self._base_dir, 'transcript')
            os.makedirs(self._transcript_dir, exist_ok=True)
        except Exception:
            self._transcript_dir = self._base_dir
        meta = load_meta()
        self.root.title(meta["title"])  # e.g., OCaption v1.0
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        # Use bundled icon for the window title bar
        try:
            self.root.iconbitmap(meta["icon"])  # from app_meta.json
        except Exception:
            pass

        self.is_recording = False
        self.caption_text = ""
        self.autosave_enabled = False
        self.autosave_path = None

        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI components"""

        # Input source: Windows Live Captions only (button to open system Live Captions)
        device_frame = ttk.LabelFrame(self.root, text="Input Source")
        device_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(device_frame, text="Windows Live Captions (built-in)").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.open_live_btn = ttk.Button(device_frame, text="Manualy Open Live Captions", command=self.start_windows_live_captions)
        self.open_live_btn.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Control buttons frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_btn = ttk.Button(button_frame, text="Start Captioning", command=self.start_recording)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Stop Captioning", command=self.stop_recording, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Autosave display placed next to Stop button
        try:
            self.autosave_label = ttk.Label(button_frame, text="Saved cleaned autosave:")
            self.autosave_label.pack(side=tk.LEFT, padx=(10,2))
            # Use tk.Button so we can change the text color to blue for a link
            try:
                self.autosave_button = tk.Button(button_frame, text="(none)", state=tk.DISABLED, fg='blue')
                self.autosave_button.pack(side=tk.LEFT, padx=2)
            except Exception:
                # fallback to ttk if tk.Button isn't available
                self.autosave_button = ttk.Button(button_frame, text="(none)", state=tk.DISABLED)
                self.autosave_button.pack(side=tk.LEFT, padx=2)
        except Exception:
            self.autosave_button = None

        # Clear button placed last with red text
        try:
            self.clear_btn = tk.Button(button_frame, text="Clear Text", fg="red", command=self.clear_captions)
            self.clear_btn.pack(side=tk.LEFT, padx=5)
        except Exception:
            # fallback to ttk if tk.Button fails
            try:
                self.clear_btn = ttk.Button(button_frame, text="Clear Text", command=self.clear_captions)
                self.clear_btn.pack(side=tk.LEFT, padx=5)
            except Exception:
                self.clear_btn = None

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, foreground="green").pack(anchor=tk.W, padx=10)

        # Caption display
        caption_frame = ttk.LabelFrame(self.root, text="Live Captions")
        caption_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.caption_display = scrolledtext.ScrolledText(
            caption_frame,
            height=15,
            width=70,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#f0f0f0"
        )
        self.caption_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # autosave widgets are shown in the control button frame

        # tag for autosave link (clickable)
        try:
            self.caption_display.tag_configure('autosave_link', foreground='blue', underline=1)
        except Exception:
            pass

        # Actions frame
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Auto-scroll toggle
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.autoscroll_chk = ttk.Checkbutton(action_frame, text="Auto-scroll", variable=self.autoscroll_var)
        self.autoscroll_chk.pack(side=tk.LEFT, padx=5)

        # Export buttons removed by request
        
    # device enumeration removed; Live Captions is the only input source

    def start_windows_live_captions(self):
        """Attempt to trigger Windows Live Captions via Win+Ctrl+L keypress.

        If the synthetic keypress fails, instruct the user to press Win+Ctrl+L manually.
        """
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            VK_LWIN = 0x5B
            VK_CONTROL = 0x11
            VK_L = 0x4C
            KEYEVENTF_KEYUP = 0x0002

            # Press Win + Ctrl + L
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_L, 0, 0, 0)

            # Release in reverse order
            user32.keybd_event(VK_L, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

            # Update status quietly instead of showing a popup
            try:
                self.status_var.set("Live Captions (MANUAL ACTIVATION: Press Win+Ctrl+L)")
            except Exception:
                pass
        except Exception:
            # Silently fail and set status so user can press the hotkey manually
            try:
                self.status_var.set("Press Win+Ctrl+L to open Live Captions")
            except Exception:
                pass

    def _show_autosave_link(self, path: str):
        """Insert or replace a clickable autosave path at the top of the caption display."""
        if not path:
            return

        try:
            # remove existing top-line if it looks like an autosave link (heuristic)
            try:
                first_line = self.caption_display.get('1.0', '1.end')
                if first_line.startswith('Autosave:') or first_line.startswith('Saved:') or first_line.startswith('File:'):
                    self.caption_display.delete('1.0', '2.0')
            except Exception:
                pass

            basename = os.path.basename(path)

            # If an external autosave button exists, update it and bind to open the file
            try:
                if hasattr(self, 'autosave_button') and getattr(self, 'autosave_button') is not None:
                    try:
                        self.autosave_button.config(text=basename, state=tk.NORMAL)

                        def _open_file(p=path):
                            try:
                                os.startfile(p)
                            except Exception:
                                try:
                                    os.startfile(os.path.dirname(p))
                                except Exception:
                                    pass

                        try:
                            self.autosave_button.config(command=_open_file)
                        except Exception:
                            pass
                        return
                    except Exception:
                        pass
            except Exception:
                pass

            # Fallback: insert link into the transcript if the external bar isn't available
            link_line = f"Autosave: {path}\n"
            try:
                self.caption_display.insert('1.0', link_line)
                self.caption_display.tag_add('autosave_link', '1.0', '1.end')
                try:
                    self.caption_display.tag_config('autosave_link', foreground='blue', underline=1)
                except Exception:
                    pass

                def _open(e, p=path):
                    try:
                        os.startfile(p)
                    except Exception:
                        try:
                            os.startfile(os.path.dirname(p))
                        except Exception:
                            pass

                try:
                    self.caption_display.tag_unbind('autosave_link', '<Button-1>')
                except Exception:
                    pass
                self.caption_display.tag_bind('autosave_link', '<Button-1>', _open)
            except Exception:
                pass
        except Exception:
            pass

    # on_source_change and get_selected_device_ids removed
    
    def start_recording(self):
        """Start reading Windows Live Captions (only input)."""
        if LiveCaptionReader is None:
            messagebox.showerror("Error", "Live Captions reader not available (pywinauto missing)")
            return

        # Clear any previous autosave link/button when starting a new session
        try:
            if hasattr(self, 'autosave_button') and getattr(self, 'autosave_button') is not None:
                try:
                    self.autosave_button.config(text='(none)', state=tk.DISABLED, fg='blue', cursor='')
                except Exception:
                    try:
                        self.autosave_button.config(text='(none)', state=tk.DISABLED)
                    except Exception:
                        pass
        except Exception:
            pass

        # Clear transcript window and live-state for a fresh session
        try:
            try:
                self.caption_display.delete(1.0, tk.END)
            except Exception:
                pass
            self.caption_text = ""
            try:
                self._live_shown_text = ''
            except Exception:
                pass
            try:
                self._last_live_update = 0
            except Exception:
                pass
        except Exception:
            pass

        try:
            self.lc_reader = LiveCaptionReader()
            self.lc_reader.on_change = lambda t: self.root.after(0, self.on_live_text, t)
            self._live_active = True
            if not self.caption_display.get(1.0, tk.END).strip():
                self.caption_display.insert(tk.END, "\n")

            # Start the reader thread so it can detect the control if opened shortly after.
            try:
                self.lc_reader.start()
            except Exception:
                pass

            # First, try a quick direct read of current text (non-blocking). If empty,
            # launch Live Captions (Win+Ctrl+L) and wait for control text up to 5s.
            full = ""
            try:
                full = self.lc_reader.get_current_text(timeout=0.5, poll=0.15).strip()
            except Exception:
                full = getattr(self.lc_reader, 'latest_text', '').strip()

            if not full:
                try:
                    self.start_windows_live_captions()
                except Exception:
                    pass

                try:
                    full = self.lc_reader.get_current_text(timeout=5.0, poll=0.2).strip()
                except Exception:
                    full = getattr(self.lc_reader, 'latest_text', '').strip()

            # If we obtained initial content, append it as a permanent transcript line
            try:
                if full:
                    parts = [p.strip() for p in re.split(r"\r?\n", full) if p.strip()]
                    initial_text = ' '.join(parts) if parts else full

                    if initial_text and len(initial_text) > 3:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        caption_line = f"[{timestamp}] {initial_text}\n"
                        self.append_caption(caption_line, replace_last=False)
                        self.caption_text += caption_line
                        try:
                            self._live_shown_text = initial_text
                        except Exception:
                            self._live_shown_text = ''
                        self._last_live_update = time.time()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Live Captions reader:\n{e}")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Reading Windows Live Captions...")

        # Setup autosave file in transcript folder
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.autosave_path = os.path.join(self._transcript_dir, f"{ts}.txt")
            with open(self.autosave_path, 'a', encoding='utf-8') as f:
                f.write(f"[Recording started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
            self.autosave_enabled = True
        except Exception:
            self.autosave_enabled = False
            self.autosave_path = None
    
    def append_caption(self, text, replace_last=False):
        """Append or replace the last live-caption block.

        If `replace_last` is True, the method will replace the last live-caption block
        inserted by the LiveCaptionReader instead of appending a new line. This prevents
        repeated identical lines from accumulating.
        """
        try:
            # decide whether to auto-scroll after inserting
            try:
                _, view_end = self.caption_display.yview()
            except Exception:
                view_end = 1.0
            autoscroll_enabled = bool(getattr(self, 'autoscroll_var', tk.BooleanVar(value=True)).get())
            was_at_bottom = autoscroll_enabled and view_end >= 0.99

            if replace_last:
                # use a text tag to mark the live block so we can replace it cleanly
                # replace the last line in the text widget so live updates don't accumulate
                try:
                    last_line_start = self.caption_display.index('end-1c linestart')
                except Exception:
                    last_line_start = None

                if last_line_start is None:
                    # just insert
                    self.caption_display.insert(tk.END, text)
                else:
                    try:
                        # delete the last line
                        self.caption_display.delete(last_line_start, tk.END)
                    except Exception:
                        pass
                    # insert new live text followed by newline
                    self.caption_display.insert(tk.END, text)
            else:
                # Normal append — if live is active, insert the permanent text above the live line
                try:
                    if getattr(self, '_live_active', False):
                        try:
                            insert_pos = self.caption_display.index('end-1c linestart')
                        except Exception:
                            insert_pos = tk.END
                        # insert the permanent caption before the live line
                        try:
                            self.caption_display.insert(insert_pos, text)
                        except Exception:
                            self.caption_display.insert(tk.END, text)
                    else:
                        self.caption_display.insert(tk.END, text)
                except Exception:
                    self.caption_display.insert(tk.END, text)

            if was_at_bottom:
                try:
                    self.caption_display.see(tk.END)
                except Exception:
                    pass

            # Autosave: append new content to transcript file
            try:
                if self.autosave_enabled and self.autosave_path and not replace_last:
                    with open(self.autosave_path, 'a', encoding='utf-8') as f:
                        f.write(text)
            except Exception:
                pass
        except Exception:
            # best-effort append
            try:
                self.caption_display.insert(tk.END, text)
                try:
                    if getattr(self, 'autoscroll_var', tk.BooleanVar(value=True)).get():
                        self.caption_display.see(tk.END)
                except Exception:
                    pass
            except Exception:
                pass
    
    def stop_recording(self):
        """Stop recording audio"""
        # stop microphone recording if active
        self.is_recording = False

        # stop live captions reader if active
        try:
            if hasattr(self, 'lc_reader') and self.lc_reader:
                try:
                    self.lc_reader.stop()
                except Exception:
                    pass
                self.lc_reader = None
        except Exception:
            pass

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        # no device controls to re-enable (Live Captions only)

        self.status_var.set("Stopped")

        # finalize autosave
        try:
            if self.autosave_enabled and self.autosave_path:
                # append stopped marker
                try:
                    with open(self.autosave_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n[Recording stopped {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                except Exception:
                    pass

                # Use the same cleaning logic as Export Cleaned but write silently to the autosave file
                try:
                    display_text = self.caption_display.get(1.0, tk.END).strip()
                    cleaned = self.clean_text(display_text)

                    # If cleaning the display produced nothing, fallback to cleaning the raw autosave content
                    if not cleaned:
                        try:
                            with open(self.autosave_path, 'r', encoding='utf-8') as f:
                                raw = f.read()
                            cleaned = self.clean_text(raw)
                        except Exception:
                            cleaned = ''

                    if cleaned:
                        try:
                            with open(self.autosave_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned)
                        except Exception:
                            pass

                        # show path as clickable link at top of transcript window
                        try:
                            self._show_autosave_link(self.autosave_path)
                        except Exception:
                            pass

                        # Update status to indicate cleaned autosave was written (no prompt)
                        try:
                            self.status_var.set(f"Saved cleaned autosave: {os.path.basename(self.autosave_path)}")
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self.autosave_enabled = False
            self.autosave_path = None

    def on_live_text(self, raw_text):
        """Sanitize live caption updates - accumulative append strategy.

        Live Captions sends full transcript repeatedly. Strategy:
        - Track all text we've already shown
        - Extract only words that haven't been displayed yet
        - Append new content (don't replace)
        - Rate limit to prevent spam (max 2 updates/sec)
        """
        try:
            import time
            
            if not raw_text or len(raw_text.strip()) < 5:
                return

            # Rate limiting: skip if updated too recently (within 500ms)
            now = time.time()
            last_update = getattr(self, '_last_live_update', 0)
            if now - last_update < 0.5:
                return

            s = raw_text.strip()

            # remove control tokens and normalize
            s = re.sub(r"\binstructions\[LiveCaptions\]\s*\d+\b", "", s, flags=re.IGNORECASE)
            s = re.sub(r"\s+", " ", s).strip()

            # collapse repeated consecutive words
            s = re.sub(r"\b(\w+)(?:\s+\1\b){2,}", r"\1", s, flags=re.IGNORECASE)

            if len(s) < 8:
                return

            # Track cumulative shown text (all words we've displayed)
            shown_text = getattr(self, '_live_shown_text', '')
            
            if shown_text:
                # Compare word-by-word to find where shown text ends and new begins
                shown_words = shown_text.split()
                curr_words = s.split()
                
                # Find where current text matches end of shown text
                # (Live Captions might edit, so check if shown is a subsequence)
                match_idx = 0
                if len(shown_words) > 0:
                    # Find where shown_words appear in curr_words
                    for i in range(len(curr_words)):
                        # Check if remaining curr_words start with a suffix of shown_words
                        for j in range(len(shown_words)):
                            tail_shown = shown_words[j:]
                            if i + len(tail_shown) <= len(curr_words):
                                matches = all(
                                    tail_shown[k].lower().rstrip('.,!?;:') == 
                                    curr_words[i+k].lower().rstrip('.,!?;:')
                                    for k in range(len(tail_shown))
                                )
                                if matches:
                                    match_idx = i + len(tail_shown)
                                    break
                        if match_idx > 0:
                            break
                
                # Extract new words
                if match_idx < len(curr_words):
                    new_words = curr_words[match_idx:]
                else:
                    # No new content found
                    return
                
                new_text = ' '.join(new_words).strip()
                
                # Only append if substantial (3+ words)
                if len(new_words) < 3:
                    return
                
                display_text = new_text
                
                # Update cumulative shown text
                self._live_shown_text = shown_text + ' ' + new_text
            else:
                # First update - show last ~10 words
                words = s.split()
                if len(words) > 10:
                    display_text = ' '.join(words[-10:])
                else:
                    display_text = s
                
                self._live_shown_text = display_text

            # Update timestamp
            self._last_live_update = now
            
            # Append new text (not replace - we're building a transcript)
            display_text = display_text.strip()
            if display_text and len(display_text) > 5:
                # Remove the _live_active flag so we append normally
                was_live = getattr(self, '_live_active', False)
                self._live_active = False
                self.append_caption(display_text + " ", replace_last=False)
                self._live_active = was_live

        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def clear_captions(self):
        """Clear all captions"""
        self.caption_display.delete(1.0, tk.END)
        self.caption_text = ""

    def clean_text(self, raw_text: str) -> str:
        """Save captions to a text file"""
        text = self.caption_display.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No captions to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~\\Documents"),
            initialfile=f"captions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("Success", f"Captions saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def clean_text(self, raw_text: str) -> str:
        """Remove repeated words and near-duplicate sentences from text.

        - Collapses repeated words (e.g., "in in", "the the")
        - Deduplicates sentences by normalized form
        - Skips near-duplicates with high token overlap
        """
        if not raw_text:
            return ""

        # Remove known Live Captions default/placeholder messages that appear when
        # there's no audio. Keep this list conservative; match case-insensitively.
        try:
            noise_patterns = [
                r"Ready to show live captions in [^\r\n]*",
            ]
            for pat in noise_patterns:
                raw_text = re.sub(pat, "", raw_text, flags=re.IGNORECASE)
        except Exception:
            pass

        s = re.sub(r"\s+", " ", raw_text).strip()
        # collapse repeated consecutive words (case-insensitive)
        s = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", s, flags=re.IGNORECASE)

        # split into sentences (keep punctuation)
        parts = re.split(r"(?<=[\.!?])\s+", s)
        cleaned = []
        seen = set()

        def norm(sent: str) -> str:
            return re.sub(r"[^a-z0-9 ]+", "", sent.lower()).strip()

        for sent in parts:
            t = sent.strip()
            if not t:
                continue
            k = norm(t)
            if not k or len(k) < 3:
                continue
            if k in seen:
                continue

            # near-duplicate check vs previous kept sentence
            if cleaned:
                prev_k = norm(cleaned[-1])
                A = set(prev_k.split())
                B = set(k.split())
                if B:
                    overlap = len(A & B) / len(B)
                    if overlap > 0.85:
                        # too similar to previous, skip
                        continue

            seen.add(k)
            cleaned.append(t)

        return " ".join(cleaned).strip()

def main():
    root = tk.Tk()
    app = CaptionerApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl-C
        try:
            app.stop_recording()
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    main()
