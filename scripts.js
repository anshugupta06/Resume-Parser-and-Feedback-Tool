document.getElementById('uploadButton').addEventListener('click', async () => {
    const fileInput = document.getElementById('file-upload');
    if (!fileInput.files.length) {
        alert('Please select a file!');
        return;
    }

    const file = fileInput.files[0];

    // Show the feedback section once the process starts
    document.getElementById("feedbackSection").style.display = "block";
    
    // Create FormData object to send the file
    const formData = new FormData();
    formData.append('resume', file);

    try {
        // Send the data to the Flask backend
        const response = await fetch('/upload_resume', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to upload resume');
        }

        const result = await response.json();

        const atsScore = result.ats_score;  // Assuming ats_score is returned from the backend
        const feedback = result.feedback;  // Assuming feedback is returned as an array from the backend

        // Simulate progress bar update
        let progress = 0;
        const progressBar = document.getElementById('progressBar');
        const interval = setInterval(() => {
            progress += 10;
            progressBar.style.width = `${progress}%`;
            progressBar.innerText = `${progress}%`;
            if (progress === 100) {
                clearInterval(interval);
                
                // Update the ATS score and feedback after progress bar reaches 100%
                document.getElementById('atsScore').innerText = `ATS Score: ${atsScore}`;
                document.getElementById('feedback').innerText = feedback.join(", ");
            }
        }, 1000);
    } catch (error) {
        alert('Error uploading resume: ' + error.message);
    }
});
