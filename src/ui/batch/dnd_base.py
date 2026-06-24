import logging
import customtkinter as ctk

logger = logging.getLogger("PrivaSub.DnDBase")

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_TKDND = True
except ImportError:
    HAS_TKDND = False

if HAS_TKDND:
    class FileTranscriberBase(ctk.CTkToplevel, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.tkdnd_active = True
            except Exception as e:
                logger.warning(f"Failed to load TkinterDnD extension: {e}. Falling back to click-to-select.")
                self.tkdnd_active = False
else:
    class FileTranscriberBase(ctk.CTkToplevel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tkdnd_active = False
