import os
import logging
import tempfile
import uuid
import re
import json
import subprocess
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import yt_dlp
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import db instance
from models import db

# Initialize the database with the app
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Directory for temporary storage of downloads
TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/video_info', methods=['POST'])
def get_video_info():
    """Get video information based on the URL using yt-dlp"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. JSON required.'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
        
    video_url = data.get('url', '')
    if not video_url:
        return jsonify({'error': 'Missing video URL'}), 400
    
    # Validate URL
    if not is_valid_youtube_url(video_url):
        return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube video URL.'}), 400
    
    try:
        # Try to extract video ID directly for logging
        video_id = extract_video_id(video_url)
        if video_id:
            logger.debug(f"Attempting to fetch video with ID: {video_id}")
        
        # Set up yt-dlp options to extract information only (no download)
        ydl_opts = {
            'format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,  # Don't download, just get info
            'forcejson': True,      # Force JSON output
            'simulate': True,       # Just simulate, don't download
            'noplaylist': True,     # Single video, not a playlist
        }
        
        # Use yt-dlp to extract video information
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return jsonify({'error': 'Could not retrieve video information. The video might be unavailable.'}), 400
                
            # Extract essential information
            title = info.get('title', 'Unknown Title')
            author = info.get('uploader', 'Unknown Author')
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')
            
            # Check if we have valid data
            if not all([title, author, duration, thumbnail]):
                logger.warning(f"Incomplete video info: title={title}, author={author}, duration={duration}")
                # Continue anyway as we might have some formats
            
            # Generate formats list with quality options
            stream_options = []
            formats = info.get('formats', [])
            
            # Filter for mp4 formats with both video and audio
            for format_info in formats:
                # Skip formats without video
                if not format_info.get('height') or format_info.get('vcodec') == 'none':
                    continue
                    
                # Skip audio-only formats
                if format_info.get('acodec') == 'none':
                    continue
                    
                # Skip non-mp4 formats for simplicity (we can expand later)
                if format_info.get('ext') != 'mp4':
                    continue
                    
                format_id = format_info.get('format_id')
                height = format_info.get('height')
                filesize = format_info.get('filesize')
                
                # Only add formats with all required information
                if format_id and height:
                    resolution = f"{height}p"
                    
                    # Calculate filesize in MB if available
                    if filesize:
                        filesize_mb = round(filesize / (1024 * 1024), 2)
                        filesize_str = f"{filesize_mb} MB"
                    else:
                        filesize_str = "Unknown"
                        
                    stream_options.append({
                        'itag': format_id,  # Use format_id as itag for compatibility
                        'resolution': resolution,
                        'filesize': filesize_str
                    })
            
            # If no valid formats found, return error
            if not stream_options:
                return jsonify({'error': 'No downloadable formats found for this video. It may be protected or restricted.'}), 400
            
            # Sort by resolution (height) - highest first
            stream_options = sorted(stream_options, 
                                   key=lambda x: int(x['resolution'].replace('p', '')) if x['resolution'].replace('p', '').isdigit() else 0, 
                                   reverse=True)
            
            # Generate a session ID for this download
            download_id = str(uuid.uuid4())
            session[download_id] = {
                'url': video_url,
                'video_id': video_id if video_id else 'unknown'
            }
            
            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'author': author,
                'streams': stream_options,
                'download_id': download_id
            })
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'This video is unavailable or restricted. Please try another video.'}), 400
    except yt_dlp.utils.ExtractorError as e:
        logger.error(f"Extractor error: {str(e)}")
        return jsonify({'error': 'Could not extract video information. The video might be unavailable.'}), 400
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': 'Network error when connecting to YouTube. Please check your connection and try again.'}), 500
    except Exception as e:
        logger.error(f"Error getting video info: {type(e).__name__}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while processing your request. Please try again later.'}), 500

@app.route('/download', methods=['POST'])
def download_video():
    """Download the video with the selected quality using yt-dlp"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. JSON required.'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
        
    download_id = data.get('download_id')
    format_id = data.get('itag')  # Using itag parameter for compatibility with frontend
    
    if not download_id or not format_id:
        return jsonify({'error': 'Missing download ID or format ID'}), 400
    
    # Get the URL from the session
    if download_id not in session:
        return jsonify({'error': 'Invalid download session'}), 400
    
    video_url = session[download_id]['url']
    
    try:
        # Create a unique filename with a timestamp to avoid collisions
        timestamp = uuid.uuid4().hex[:8]
        temp_filename = f"youtube_video_{timestamp}.mp4"
        file_path = os.path.join(TEMP_DIR, temp_filename)
        
        logger.debug(f"Attempting to download video from URL: {video_url} with format ID: {format_id}")
        
        # Configure yt-dlp options for downloading
        ydl_opts = {
            'format': format_id,
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,     # Single video, not a playlist
            'noprogress': False     # Show progress
        }
        
        # Download the video with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get the title
            info = ydl.extract_info(video_url, download=False)
            if not info:
                return jsonify({'error': 'Could not retrieve video information for download'}), 400
                
            # Get proper video title and create a better filename
            title = info.get('title', 'Unknown Video')
            resolution = next((f"{fmt.get('height')}p" for fmt in info.get('formats', []) 
                              if fmt.get('format_id') == format_id and fmt.get('height')), "unknown")
            
            # Create a better final filename
            sanitized_title = sanitize_filename(title)
            final_filename = f"{sanitized_title}_{resolution}_{timestamp}.mp4"
            
            # Download the video
            logger.debug(f"Downloading video to: {file_path}")
            ydl.download([video_url])
            
            # Verify the file was downloaded successfully
            if not os.path.exists(file_path):
                return jsonify({'error': 'Download failed. The file was not created.'}), 500
                
            # Verify file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                os.remove(file_path)  # Clean up empty file
                return jsonify({'error': 'Download failed. The file is empty.'}), 500
            
            # Store the file path and final filename in the session for download
            session[download_id]['file_path'] = file_path
            session[download_id]['filename'] = final_filename
            
            logger.debug(f"Download successful. File size: {file_size} bytes")
            return jsonify({
                'success': True,
                'download_id': download_id,
                'filename': final_filename
            })
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'This video could not be downloaded. It may be unavailable or restricted.'}), 400
    except yt_dlp.utils.ExtractorError as e:
        logger.error(f"Extractor error: {str(e)}")
        return jsonify({'error': 'Could not extract video information for download.'}), 400
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': 'Network error when connecting to YouTube. Please check your connection and try again.'}), 500
    except Exception as e:
        logger.error(f"Error downloading video: {type(e).__name__}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during download. Please try again later.'}), 500

@app.route('/get_file/<download_id>', methods=['GET'])
def get_file(download_id):
    """Serve the downloaded file to the user"""
    if download_id not in session:
        return "Download session expired or invalid", 400
    
    file_info = session.get(download_id, {})
    file_path = file_info.get('file_path')
    filename = file_info.get('filename')
    
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return f"Error serving file: {str(e)}", 500
    finally:
        # Clean up the temp file after sending
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing temp file: {str(e)}")

def extract_video_id(url):
    """Extract the YouTube video ID from a URL"""
    try:
        # Check for youtu.be format
        if 'youtu.be' in url:
            return url.split('/')[-1].split('?')[0]
        
        # Check for youtube.com format
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
        
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None

def is_valid_youtube_url(url):
    """Validate if the URL is a YouTube URL"""
    try:
        parsed_url = urlparse(url)
        # Check for valid YouTube domains
        valid_domains = ('youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com')
        if parsed_url.netloc in valid_domains:
            # For youtube.com, ensure it has a 'v' parameter or '/watch' path
            if parsed_url.netloc in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
                if '/watch' not in parsed_url.path and 'v=' not in parsed_url.query:
                    return False
            # For youtu.be, ensure it has something after the domain
            elif parsed_url.netloc == 'youtu.be' and not parsed_url.path[1:]:
                return False
            return True
        return False
    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}")
        return False

def sanitize_filename(filename):
    """Remove invalid characters from the filename"""
    # Replace any character that's not alphanumeric, space, hyphen, or underscore
    import re
    return re.sub(r'[^\w\s-]', '_', filename)[:100]  # Also truncate to reasonable length

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
