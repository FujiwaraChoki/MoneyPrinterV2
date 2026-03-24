import os
import requests

from utils import info, success, error, warning
from config import get_verbose


class UploadPost:
    """
    Class for cross-posting videos to TikTok and Instagram via Upload-Post API.
    
    Docs: https://docs.upload-post.com
    """

    API_BASE = "https://api.upload-post.com"

    def __init__(self, api_key: str, username: str) -> None:
        """
        Constructor for UploadPost Class.

        Args:
            api_key (str): Upload-Post API key
            username (str): Upload-Post username/profile

        Returns:
            None
        """
        self._api_key = api_key
        self._username = username

    def upload_video(
        self,
        video_path: str,
        title: str,
        platforms: list = ["tiktok", "instagram"],
        privacy_level: str = "PUBLIC_TO_EVERYONE"
    ) -> dict:
        """
        Uploads a video to TikTok and/or Instagram via Upload-Post API.

        Args:
            video_path (str): Path to the video file
            title (str): Video title/caption
            platforms (list): List of platforms to upload to (tiktok, instagram)
            privacy_level (str): Privacy level for the video

        Returns:
            response (dict): API response with request_id
        """
        if not os.path.exists(video_path):
            error(f"Video file not found: {video_path}")
            return None

        if get_verbose():
            info(f"Uploading video to {', '.join(platforms)} via Upload-Post...")

        try:
            # Prepare multipart form data
            files = {
                'video': open(video_path, 'rb')
            }
            
            data = {
                'user': self._username,
                'title': title[:2200],  # Instagram caption limit
                'privacy_level': privacy_level
            }
            
            # Add platforms
            for platform in platforms:
                data[f'platform[]'] = platform

            headers = {
                'Authorization': f'Apikey {self._api_key}'
            }

            response = requests.post(
                f"{self.API_BASE}/api/upload_video",
                headers=headers,
                data=data,
                files=files,
                timeout=300
            )
            
            files['video'].close()
            
            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                success(f"Video uploaded successfully!")
                success(f"Request ID: {result.get('request_id')}")
                
                if get_verbose():
                    info(f"Platforms: {', '.join(platforms)}")
                    
                return result
            else:
                error(f"Upload failed: {result.get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            error(f"Failed to upload video: {str(e)}")
            return None

    def check_status(self, request_id: str) -> dict:
        """
        Check the status of an upload request.

        Args:
            request_id (str): The request ID from upload_video

        Returns:
            status (dict): Status information
        """
        try:
            headers = {
                'Authorization': f'Apikey {self._api_key}'
            }

            response = requests.get(
                f"{self.API_BASE}/api/status/{request_id}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error(f"Failed to check status: {str(e)}")
            return None
