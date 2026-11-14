/**
 * Smart Class Complaint System - Client-side Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 1. Textarea Character Counter & Privacy Warning Scanner
  const descInput = document.getElementById('description');
  const charCounter = document.getElementById('charCount');
  const privacyAlert = document.getElementById('privacyWarningNotice');

  if (descInput && charCounter) {
    const minChars = 10;
    const maxChars = 3000;

    function updateCounterAndScan() {
      const text = descInput.value;
      const count = text.length;
      charCounter.textContent = `${count} / ${maxChars} characters`;

      if (count < minChars) {
        charCounter.classList.add('text-danger');
        charCounter.classList.remove('text-success', 'text-muted');
      } else if (count > maxChars) {
        charCounter.classList.add('text-danger');
      } else {
        charCounter.classList.remove('text-danger');
        charCounter.classList.add('text-muted');
      }

      // Privacy Scanner: detect accidental inclusion of phone numbers or email addresses
      if (privacyAlert) {
        const phoneRegex = /(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b/;
        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

        if (phoneRegex.test(text) || emailRegex.test(text)) {
          privacyAlert.classList.remove('d-none');
        } else {
          privacyAlert.classList.add('d-none');
        }
      }
    }

    descInput.addEventListener('input', updateCounterAndScan);
    updateCounterAndScan();
  }

  // 2. Custom Location Toggle
  const locationSelect = document.getElementById('locationSelect');
  const customLocationWrapper = document.getElementById('customLocationWrapper');
  const customLocationInput = document.getElementById('customLocationInput');

  if (locationSelect && customLocationWrapper) {
    locationSelect.addEventListener('change', function () {
      if (this.value === '__custom__') {
        customLocationWrapper.classList.remove('d-none');
        if (customLocationInput) customLocationInput.focus();
      } else {
        customLocationWrapper.classList.add('d-none');
      }
    });
  }

  // 3. Copy to Clipboard Functionality
  const copyButtons = document.querySelectorAll('.btn-copy-id');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const textToCopy = this.getAttribute('data-clipboard-text') || this.textContent.trim();
      if (!textToCopy) return;

      navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="bi bi-check2"></i> Copied!';
        this.classList.remove('btn-outline-primary', 'btn-outline-secondary');
        this.classList.add('btn-success');

        setTimeout(() => {
          this.innerHTML = originalText;
          this.classList.remove('btn-success');
          this.classList.add('btn-outline-primary');
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    });
  });

  // 4. Form Validation Check
  const complaintForm = document.getElementById('complaintForm');
  if (complaintForm) {
    complaintForm.addEventListener('submit', function (e) {
      const desc = descInput ? descInput.value.trim() : '';
      if (!desc || desc.length < 10) {
        e.preventDefault();
        alert('Please describe your issue with at least 10 characters.');
        if (descInput) descInput.focus();
        return false;
      }
    });
  }
});
