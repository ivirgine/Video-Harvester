document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const urlForm = document.getElementById('url-form');
    const videoUrlInput = document.getElementById('video-url');
    const loadingElement = document.getElementById('loading');
    const errorMessageElement = document.getElementById('error-message');
    const videoInfoElement = document.getElementById('video-info');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoTitle = document.getElementById('video-title');
    const videoAuthor = document.getElementById('video-author');
    const videoDuration = document.getElementById('video-duration');
    const qualityOptions = document.getElementById('quality-options');
    const downloadProgressContainer = document.getElementById('download-progress-container');
    const downloadProgress = document.getElementById('download-progress');
    const downloadStatus = document.getElementById('download-status');
    const downloadComplete = document.getElementById('download-complete');
    const downloadLink = document.getElementById('download-link');
    
    // Current video data
    let currentDownloadId = null;

    // Handle URL form submission
    urlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const url = videoUrlInput.value.trim();
        
        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }
        
        // Reset UI
        resetUI();
        
        // Show loading spinner
        loadingElement.classList.remove('d-none');
        
        // Fetch video info
        fetchVideoInfo(url);
    });
    
    // Fetch video information
    function fetchVideoInfo(url) {
        fetch('/video_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingElement.classList.add('d-none');
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Save download ID
            currentDownloadId = data.download_id;
            
            // Display video information
            displayVideoInfo(data);
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Error fetching video information: ' + error.message);
        });
    }
    
    // Display video information
    function displayVideoInfo(data) {
        // Set video details
        videoThumbnail.src = data.thumbnail;
        videoTitle.textContent = data.title;
        videoAuthor.textContent = `by ${data.author}`;
        videoDuration.textContent = formatDuration(data.duration);
        
        // Create quality options
        qualityOptions.innerHTML = '';
        data.streams.forEach(stream => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const infoDiv = document.createElement('div');
            infoDiv.innerHTML = `
                <strong>${stream.resolution}</strong>
                <span class="ms-2 text-muted">(${stream.filesize})</span>
            `;
            
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-primary download-btn';
            downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i> Download';
            downloadBtn.addEventListener('click', () => {
                downloadVideo(data.download_id, stream.itag);
            });
            
            item.appendChild(infoDiv);
            item.appendChild(downloadBtn);
            qualityOptions.appendChild(item);
        });
        
        // Show video info section
        videoInfoElement.classList.remove('d-none');
        videoInfoElement.classList.add('fade-in');
    }
    
    // Download video
    function downloadVideo(downloadId, itag) {
        // Show download progress
        downloadProgressContainer.classList.remove('d-none');
        downloadComplete.classList.add('d-none');
        videoInfoElement.classList.add('d-none');
        
        // Update progress bar to show indeterminate progress
        downloadProgress.style.width = '100%';
        downloadStatus.textContent = 'Preparing your download...';
        
        // Request download
        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                download_id: downloadId,
                itag: itag
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                downloadProgressContainer.classList.add('d-none');
                return;
            }
            
            // Download is ready
            downloadProgressContainer.classList.add('d-none');
            downloadComplete.classList.remove('d-none');
            
            // Set download link
            downloadLink.href = `/get_file/${data.download_id}`;
            downloadLink.setAttribute('download', data.filename);
        })
        .catch(error => {
            downloadProgressContainer.classList.add('d-none');
            showError('Error downloading video: ' + error.message);
        });
    }
    
    // Helper function to format duration
    function formatDuration(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        let result = '';
        if (hrs > 0) {
            result += `${hrs}h `;
        }
        if (mins > 0) {
            result += `${mins}m `;
        }
        result += `${secs}s`;
        
        return result;
    }
    
    // Show error message
    function showError(message) {
        errorMessageElement.textContent = message;
        errorMessageElement.classList.remove('d-none');
    }
    
    // Reset UI elements
    function resetUI() {
        errorMessageElement.classList.add('d-none');
        videoInfoElement.classList.add('d-none');
        downloadProgressContainer.classList.add('d-none');
        downloadComplete.classList.add('d-none');
        currentDownloadId = null;
    }
});
