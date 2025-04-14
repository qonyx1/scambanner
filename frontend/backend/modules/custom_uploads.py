import requests
import mimetypes
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

load_dotenv()

def upload_image(image_path):
    url = f"https://api.imgbb.com/1/upload?key={os.getenv('IMGBB_API_KEY')}"
    with open(image_path, "rb") as image_file:
        files = {
            "image": image_file,
        }
        response = requests.post(url, files=files)
        if response.status_code == 200:
            return response.json().get("data", {}).get("url")
        else:
            response.raise_for_status()

def upload_video(video_path):
    cloudinary.config(
        cloud_name=os.getenv("VIDEO_API_CLOUD_NAME"),
        api_key=os.getenv("VIDEO_API_KEY"),
        api_secret=os.getenv("VIDEO_API_SECRET"),
        secure=True
    )
    upload_result = cloudinary.uploader.upload(video_path, resource_type="video")
    return upload_result.get("secure_url") or None
