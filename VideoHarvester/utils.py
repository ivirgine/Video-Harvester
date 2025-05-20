import re
import os
import logging
from urllib.parse import urlparse
import yt_dlp

# Configure logging
logger = logging.getLogger(__name__)

def detect_source(url):
    """Detect the source platform from a URL"""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if any(youtube_domain in domain for youtube_domain in ['youtube.com', 'youtu.be']):
            return 'youtube'
        elif 'vimeo.com' in domain:
            return 'vimeo'
        elif 'dailymotion.com' in domain or 'dai.ly' in domain:
            return 'dailymotion'
        elif 'facebook.com' in domain or 'fb.watch' in domain:
            return 'facebook'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        elif 'soundcloud.com' in domain:
            return 'soundcloud'
        elif 'mixcloud.com' in domain:
            return 'mixcloud'
        else:
            return 'unknown'
    except Exception as e:
        logger.error(f"Error detecting source: {e}")
        return 'unknown'

def is_valid_url(url, source=None):
    """Validate if the URL is from a supported source"""
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
            
        # If source is specified, validate against that source
        if source and source != 'auto':
            detected = detect_source(url)
            return detected == source or detected == 'unknown'
            
        # Check if it's a supported video platform
        if detect_source(url) != 'unknown':
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def extract_video_id(url, source=None):
    """Extract the video ID from a URL based on the source"""
    if not source or source == 'auto':
        source = detect_source(url)
        
    try:
        if source == 'youtube':
            # YouTube ID extraction
            if 'youtu.be' in url:
                return url.split('/')[-1].split('?')[0]
            
            if 'youtube.com' in url:
                parsed_url = urlparse(url)
                query_params = parsed_url.query.split('&')
                for param in query_params:
                    if param.startswith('v='):
                        return param[2:]
            
            # Fallback to regex pattern for more complex URLs
            pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        elif source == 'vimeo':
            # Vimeo ID extraction (typically numeric)
            pattern = r'vimeo\.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|)(\d+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        elif source == 'dailymotion':
            # Dailymotion ID extraction (alphanumeric)
            pattern = r'dailymotion\.com\/(?:video\/|embed\/video\/)([a-zA-Z0-9]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            
            # dai.ly short URLs
            if 'dai.ly' in url:
                return url.split('/')[-1]
        
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return None

def get_best_audio_format(formats):
    """Get the best audio format from a list of formats"""
    audio_formats = []
    
    for fmt in formats:
        # Check if it's an audio-only format
        if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
            audio_formats.append(fmt)
    
    # Sort by quality (bitrate)
    audio_formats.sort(key=lambda x: x.get('abr', 0) if x.get('abr') else 0, reverse=True)
    
    if audio_formats:
        return audio_formats[0]
    return None

def sanitize_filename(filename):
    """Remove invalid characters from the filename"""
    # Replace any character that's not alphanumeric, space, hyphen, or underscore
    return re.sub(r'[^\w\s-]', '_', filename)[:100]  # Also truncate to reasonable length