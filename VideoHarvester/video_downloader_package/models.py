from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize database
db = SQLAlchemy()

class VideoDownload(db.Model):
    """Model to track video downloads"""
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(50), default='youtube')  # youtube, vimeo, dailymotion, etc.
    resolution = db.Column(db.String(20))
    file_size = db.Column(db.Float)  # Size in MB
    format_type = db.Column(db.String(20), default='video')  # video or audio
    download_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VideoDownload {self.title}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'resolution': self.resolution,
            'format_type': self.format_type,
            'file_size': self.file_size,
            'download_date': self.download_date.strftime("%Y-%m-%d %H:%M:%S")
        }

class ScheduledDownload(db.Model):
    """Model for scheduled downloads"""
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255))  # Optional until processed
    url = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(50), default='youtube')
    format_id = db.Column(db.String(20))  # Format ID to download
    format_type = db.Column(db.String(20), default='video')  # video or audio
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<ScheduledDownload {self.url}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'format_id': self.format_id,
            'format_type': self.format_type,
            'scheduled_time': self.scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
            'status': self.status,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'completed_at': self.completed_at.strftime("%Y-%m-%d %H:%M:%S") if self.completed_at else None
        }