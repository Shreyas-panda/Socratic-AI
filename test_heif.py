
from PIL import Image
from pillow_heif import register_heif_opener
import os

register_heif_opener()

# Create a dummy HEIC file or just check if we can import logic
print("HEIC support enabled")
