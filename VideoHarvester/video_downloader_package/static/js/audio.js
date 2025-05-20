document.addEventListener('DOMContentLoaded', function() {
    // DOM elements for audio tab
    const audioForm = document.getElementById('audio-form');
    const audioUrlInput = document.getElementById('audio-url');
    const audioSourceSelect = document.getElementById('audio-source-select');
    const loadingElement = document.getElementById('loading');
    const errorMessageElement = document.getElementById('error-message');
    const videoInfoElement = document.getElementById('video-info');
    
    // Handle audio form submission
    audioForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const url = audioUrlInput.value.trim();
        const source = audioSourceSelect.value;
        
        if (!url) {
            showError('Please enter a URL');
            return;
        }
        
        // Reset UI
        resetUI();
        
        // Show loading spinner
        loadingElement.classList.remove('d-none');
        
        // Fetch audio info
        fetchAudioInfo(url, source);
    });
    
    // Fetch audio information
    function fetchAudioInfo(url, source) {
        fetch('/audio_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                source: source 
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingElement.classList.add('d-none');
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Display video information (reuse the video info section)
            displayVideoInfo(data);
            
            // Update quality options to show audio formats
            updateQualityOptionsForAudio(data);
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Error fetching audio information: ' + error.message);
        });
    }
    
    // Update quality options to show audio formats
    function updateQualityOptionsForAudio(data) {
        const qualityOptions = document.getElementById('quality-options');
        qualityOptions.innerHTML = '';
        
        data.streams.forEach(stream => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const infoDiv = document.createElement('div');
            infoDiv.innerHTML = `
                <strong>${stream.format}</strong>
                <span class="ms-2 text-muted">(${stream.filesize})</span>
            `;
            
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-primary download-btn';
            downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i> Download Audio';
            downloadBtn.addEventListener('click', () => {
                downloadAudio(data.download_id, stream.itag);
            });
            
            item.appendChild(infoDiv);
            item.appendChild(downloadBtn);
            qualityOptions.appendChild(item);
        });
    }
    
    // Download audio
    function downloadAudio(downloadId, itag) {
        // Show download progress
        const downloadProgressContainer = document.getElementById('download-progress-container');
        const downloadComplete = document.getElementById('download-complete');
        const downloadProgress = document.getElementById('download-progress');
        const downloadStatus = document.getElementById('download-status');
        
        downloadProgressContainer.classList.remove('d-none');
        downloadComplete.classList.add('d-none');
        videoInfoElement.classList.add('d-none');
        
        // Update progress bar to show indeterminate progress
        downloadProgress.style.width = '100%';
        downloadStatus.textContent = 'Preparing your audio download...';
        
        // Request download
        fetch('/download_audio', {
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
            const downloadLink = document.getElementById('download-link');
            downloadLink.href = `/get_file/${data.download_id}`;
            downloadLink.setAttribute('download', data.filename);
        })
        .catch(error => {
            downloadProgressContainer.classList.add('d-none');
            showError('Error downloading audio: ' + error.message);
        });
    }
    
    // Show error message (reuse from main script)
    function showError(message) {
        errorMessageElement.textContent = message;
        errorMessageElement.classList.remove('d-none');
    }
    
    // Import these functions from the main script to avoid duplication
    // They should be made global or moved to a shared utility file
    function resetUI() {
        errorMessageElement.classList.add('d-none');
        videoInfoElement.classList.add('d-none');
        document.getElementById('download-progress-container').classList.add('d-none');
        document.getElementById('download-complete').classList.add('d-none');
    }
    
    function displayVideoInfo(data) {
        // Set video details
        document.getElementById('video-thumbnail').src = data.thumbnail;
        document.getElementById('video-title').textContent = data.title;
        document.getElementById('video-author').textContent = `by ${data.author}`;
        document.getElementById('video-duration').textContent = formatDuration(data.duration);
        
        // Show video info section
        videoInfoElement.classList.remove('d-none');
        videoInfoElement.classList.add('fade-in');
    }
    
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
});