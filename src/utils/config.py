import json
import os
from src.utils.paths import Paths

#/////////////////////////////////#
#    GLOBAL STUDIO CONFIGURATION  #
#/////////////////////////////////#

class Config:
    APP_NAME = "MANGA-CLEANER"
    VERSION = "3.2.0"

    # Deep Obsidian Theme
    COLOR_BG = "#0b0b0e"
    COLOR_PANEL = "#121217"
    COLOR_ACCENT = "#00d4ff" 
    COLOR_TEXT = "#e0e0e0"
    COLOR_TEXT_DIM = "#808085"
    COLOR_ERROR = "#ff4d4d"
    
    DEFAULT_BRUSH_SIZE = 40
    MAX_HISTORY = 20
    DEFAULT_TILE_WIDTH = 1024 

    # Export settings
    DEFAULT_JPG_QUALITY = 95      # 1-100
    DEFAULT_PNG_COMPRESSION = 6   # 0-9

    _ID_FILE = os.path.join(Paths.CACHE, "batch_id.json")
    _EXPORT_SETTINGS_FILE = os.path.join(Paths.CACHE, "export_settings.json")

    @staticmethod
    def get_next_batch_id():
        current_id = 1
        if os.path.exists(Config._ID_FILE):
            try:
                with open(Config._ID_FILE, 'r') as f:
                    data = json.load(f)
                    current_id = data.get("last_id", 0) + 1
            except:
                pass
        
        if current_id > 65535:
            current_id = 1
            
        with open(Config._ID_FILE, 'w') as f:
            json.dump({"last_id": current_id}, f)
            
        return f"batch_{current_id:05d}"

    @staticmethod
    def load_export_settings():
        """Load last-used export format and quality settings."""
        defaults = {
            "format": "jpg",
            "jpg_quality": Config.DEFAULT_JPG_QUALITY,
            "png_compression": Config.DEFAULT_PNG_COMPRESSION
        }
        if os.path.exists(Config._EXPORT_SETTINGS_FILE):
            try:
                with open(Config._EXPORT_SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge with defaults to handle missing keys
                    return {**defaults, **data}
            except:
                pass
        return defaults

    @staticmethod
    def save_export_settings(fmt, jpg_quality=None, png_compression=None):
        """Save export format and quality settings."""
        settings = Config.load_export_settings()
        settings["format"] = fmt
        if jpg_quality is not None:
            settings["jpg_quality"] = max(1, min(100, int(jpg_quality)))
        if png_compression is not None:
            settings["png_compression"] = max(0, min(9, int(png_compression)))
        try:
            with open(Config._EXPORT_SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            from src.utils.logger import logger
            logger.error(f"Failed to save export settings: {e}")
