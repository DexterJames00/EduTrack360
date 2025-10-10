// Assignment Form Handler - Prevents Double Submission
(function() {
    'use strict';
    
    let formSubmitted = false;
    let submitButton = null;
    let originalButtonHTML = '';
    
    function initializeAssignmentForm() {
        const form = document.getElementById('assignmentForm');
        if (!form) return;
        
        submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            originalButtonHTML = submitButton.innerHTML;
        }
        
        // Remove any existing event listeners
        form.removeEventListener('submit', handleAssignmentSubmit);
        
        // Add single event listener
        form.addEventListener('submit', handleAssignmentSubmit);
    }
    
    function handleAssignmentSubmit(e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        
        // Strict duplicate prevention
        if (formSubmitted) {
            console.log('Form already submitted, ignoring...');
            return false;
        }
        
        formSubmitted = true;
        disableForm();
        
        const formData = new FormData(e.target);
        
        // Frontend validation
        const startTime = formData.get('start_time');
        const endTime = formData.get('end_time');
        
        if (!startTime || !endTime) {
            showErrorModal('Missing Information', 'Please fill in both start time and end time.');
            resetForm();
            return false;
        }
        
        if (startTime >= endTime) {
            showErrorModal('Invalid Time', 'End time must be after start time.');
            resetForm();
            return false;
        }
        
        // Submit form
        fetch('/school_admin/assignments/create', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessModal('Success!', data.message);
                closeAssignmentModal();
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showErrorModal('Error', data.message);
                resetForm();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorModal('Network Error', 'Please check your connection and try again.');
            resetForm();
        });
        
        return false;
    }
    
    function disableForm() {
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating...';
        }
        
        const form = document.getElementById('assignmentForm');
        if (form) {
            // Disable all form inputs
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => input.disabled = true);
        }
    }
    
    function resetForm() {
        setTimeout(() => {
            formSubmitted = false;
            
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonHTML;
            }
            
            const form = document.getElementById('assignmentForm');
            if (form) {
                const inputs = form.querySelectorAll('input, select, button');
                inputs.forEach(input => input.disabled = false);
            }
        }, 2000); // 2 second delay
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAssignmentForm);
    } else {
        initializeAssignmentForm();
    }
    
    // Reinitialize when assignment modal is opened
    window.initializeAssignmentForm = initializeAssignmentForm;
})();