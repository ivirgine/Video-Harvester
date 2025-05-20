document.addEventListener('DOMContentLoaded', function() {
    // DOM elements for schedule tab
    const scheduleForm = document.getElementById('schedule-form');
    const scheduleUrlInput = document.getElementById('schedule-url');
    const scheduleSourceSelect = document.getElementById('schedule-source-select');
    const scheduleDateInput = document.getElementById('schedule-date');
    const scheduleTimeInput = document.getElementById('schedule-time');
    const audioOnlyCheck = document.getElementById('audio-only-check');
    const scheduleFetchBtn = document.getElementById('schedule-fetch-btn');
    const scheduleSubmitBtn = document.getElementById('schedule-submit-btn');
    const scheduleInfoDiv = document.getElementById('schedule-info');
    const errorMessageElement = document.getElementById('error-message');
    const loadingElement = document.getElementById('loading');
    
    // Set default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    scheduleDateInput.valueAsDate = tomorrow;
    
    // Set default time to current time
    const now = new Date();
    scheduleTimeInput.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    
    // Handle fetch button click
    scheduleFetchBtn.addEventListener('click', function() {
        const url = scheduleUrlInput.value.trim();
        const source = scheduleSourceSelect.value;
        
        if (!url) {
            showError('Please enter a URL');
            return;
        }
        
        // Reset UI
        scheduleInfoDiv.classList.add('d-none');
        errorMessageElement.classList.add('d-none');
        scheduleSubmitBtn.disabled = true;
        
        // Show loading spinner
        loadingElement.classList.remove('d-none');
        
        // Fetch video info for scheduling
        fetchScheduleInfo(url, source);
    });
    
    // Handle schedule form submission
    scheduleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const url = scheduleUrlInput.value.trim();
        const source = scheduleSourceSelect.value;
        const date = scheduleDateInput.value;
        const time = scheduleTimeInput.value;
        const audioOnly = audioOnlyCheck.checked;
        
        if (!url || !date || !time) {
            showError('Please fill all required fields');
            return;
        }
        
        // Show loading spinner
        loadingElement.classList.remove('d-none');
        
        // Submit schedule
        scheduleDownload(url, source, date, time, audioOnly);
    });
    
    // Fetch video info for scheduling
    function fetchScheduleInfo(url, source) {
        const apiEndpoint = audioOnlyCheck.checked ? '/audio_info' : '/video_info';
        
        fetch(apiEndpoint, {
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
            
            // Show video info
            scheduleInfoDiv.classList.remove('d-none');
            scheduleInfoDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <img src="${data.thumbnail}" alt="Thumbnail" class="img-thumbnail me-3" style="width: 100px;">
                    <div>
                        <h5>${data.title}</h5>
                        <p class="mb-0">by ${data.author}</p>
                        <p class="text-muted mb-0">Duration: ${formatDuration(data.duration)}</p>
                    </div>
                </div>
            `;
            
            // Store video info in form data attributes
            scheduleForm.dataset.videoId = data.download_id;
            scheduleForm.dataset.videoTitle = data.title;
            
            // Enable submit button
            scheduleSubmitBtn.disabled = false;
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Error fetching video information: ' + error.message);
        });
    }
    
    // Schedule download
    function scheduleDownload(url, source, date, time, audioOnly) {
        const videoId = scheduleForm.dataset.videoId;
        const videoTitle = scheduleForm.dataset.videoTitle;
        
        // Create datetime string
        const scheduledDateTime = `${date}T${time}:00`;
        
        fetch('/schedule_download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                source: source,
                video_id: videoId || '',
                title: videoTitle || '',
                scheduled_time: scheduledDateTime,
                format_type: audioOnly ? 'audio' : 'video'
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
            
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.className = 'alert alert-success';
            successMsg.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                Download scheduled successfully for ${new Date(scheduledDateTime).toLocaleString()}
            `;
            
            // Replace schedule info with success message
            scheduleInfoDiv.innerHTML = '';
            scheduleInfoDiv.appendChild(successMsg);
            
            // Reset form
            scheduleSubmitBtn.disabled = true;
            
            // Add link to view scheduled downloads
            const viewLink = document.createElement('a');
            viewLink.href = '/scheduled';
            viewLink.className = 'btn btn-info mt-3';
            viewLink.innerHTML = '<i class="fas fa-calendar me-2"></i>View Scheduled Downloads';
            scheduleInfoDiv.appendChild(viewLink);
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Error scheduling download: ' + error.message);
        });
    }
    
    // Show error message
    function showError(message) {
        errorMessageElement.textContent = message;
        errorMessageElement.classList.remove('d-none');
    }
    
    // Format duration (reused from main script)
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