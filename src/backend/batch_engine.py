import os
import cv2
from PySide6.QtCore import QObject, Signal
from src.utils.config import Config
from src.utils.paths import Paths
from src.utils.logger import logger

#/////////////////////////////////#
#    BATCH PROCESSING CONTROLLER  #
#/////////////////////////////////#

class BatchEngine(QObject):
    page_started = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.files = []
        self.current_index = 0
        self.output_dir = ""
        self.export_format = "jpg"
        self.export_quality = None

    def initialize_batch(self, file_paths, export_format, export_quality=None):
        self.files = file_paths
        self.export_format = export_format
        self.export_quality = export_quality
        self.current_index = 0
        
        batch_id = Config.get_next_batch_id()
        self.output_dir = os.path.join(Paths.PROCESSED, batch_id)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        logger.info(f"Batch Engine Ready: {self.output_dir}")
        return self.output_dir

    def get_next(self):
        if self.current_index < len(self.files):
            path = self.files[self.current_index]
            self.page_started.emit(path, self.current_index)
            return path
        return None

    def save_current(self, cv_img):
        if self.export_format.lower() == "none":
            logger.info("[+] Page processed and kept in session memory.")
            self.current_index += 1
            return self.current_index >= len(self.files)

        ext = self.export_format if self.export_format not in ["photoshop", "photopea"] else "png"
        orig_name = os.path.splitext(os.path.basename(self.files[self.current_index]))[0]
        filename = f"{orig_name}_cleaned.{ext}"
        save_path = os.path.join(self.output_dir, filename)
        
        # Handle alpha channel conversions on export
        if len(cv_img.shape) == 3 and cv_img.shape[2] == 4:
            out_bgr = cv2.cvtColor(cv_img, cv2.COLOR_RGBA2BGRA)
            if ext.lower() in ['jpg', 'jpeg']:
                out_bgr = cv2.cvtColor(out_bgr, cv2.COLOR_BGRA2BGR)
        else:
            out_bgr = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)

        # Use imencode with quality parameters for consistency with single export
        if self.export_quality is None:
            if ext.lower() in ['jpg', 'jpeg']:
                self.export_quality = Config.DEFAULT_JPG_QUALITY
            else:
                self.export_quality = Config.DEFAULT_PNG_COMPRESSION
                
        if ext.lower() in ['jpg', 'jpeg']:
            params = [cv2.IMWRITE_JPEG_QUALITY, self.export_quality]
        else:
            params = [cv2.IMWRITE_PNG_COMPRESSION, self.export_quality]
            
        try:
            is_success, buf = cv2.imencode(f".{ext}", out_bgr, params)
        except cv2.error as e:
            logger.error(f"cv2.imencode error: {e}")
            is_success = False
            
        if is_success:
            buf.tofile(save_path)
            logger.info(f"[+] Successfully Saved Cleaned: {filename} ({ext.upper()}, quality={self.export_quality})")
        else:
            logger.error(f"Failed to encode batch export: {save_path}")
        
        self.current_index += 1
        return self.current_index >= len(self.files)
