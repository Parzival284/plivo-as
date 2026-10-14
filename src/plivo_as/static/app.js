// Live dashboard interaction and event polling

let lastEventIndex = 0;
let isPolling = false;

document.addEventListener('DOMContentLoaded', () => {
  const callForm = document.getElementById('callForm');
  const phoneNumberInput = document.getElementById('phoneNumber');
  const callBtn = document.getElementById('callBtn');
  const btnText = callBtn.querySelector('.btn-text');
  const spinner = callBtn.querySelector('.spinner');
  const callAlert = document.getElementById('callAlert');
  const eventsLog = document.getElementById('eventsLog');
  const clearLogBtn = document.getElementById('clearLogBtn');

  // Trigger outbound call
  callForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const phoneNumber = phoneNumberInput.value.trim();

    if (!phoneNumber) return;

    // Reset alert & button state
    callAlert.style.display = 'none';
    callAlert.className = 'alert';
    callBtn.disabled = true;
    btnText.textContent = 'Calling...';
    spinner.style.display = 'inline-block';

    try {
      const response = await fetch('/api/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        callAlert.className = 'alert alert-success';
        callAlert.textContent = `Call queued successfully! Request UUID: ${data.request_uuid || 'N/A'}. Please answer your phone.`;
        callAlert.style.display = 'block';
        updateStepper('stepInitiated', true);
      } else {
        callAlert.className = 'alert alert-danger';
        callAlert.textContent = `Call failed: ${data.error || 'Unknown error'}`;
        callAlert.style.display = 'block';
      }
    } catch (err) {
      callAlert.className = 'alert alert-danger';
      callAlert.textContent = `Network error: ${err.message}`;
      callAlert.style.display = 'block';
    } finally {
      callBtn.disabled = false;
      btnText.textContent = 'Start Demo Call';
      spinner.style.display = 'none';
    }
  });

  // Clear log
  clearLogBtn.addEventListener('click', async () => {
    try {
      await fetch('/api/events/clear', { method: 'POST' });
      eventsLog.innerHTML = '<div class="empty-state">Waiting for call activity...</div>';
      lastEventIndex = 0;
      resetStepper();
    } catch (err) {
      console.error('Error clearing events:', err);
    }
  });

  // Start polling for events
  startEventPolling();
});

function startEventPolling() {
  if (isPolling) return;
  isPolling = true;

  setInterval(async () => {
    try {
      const res = await fetch(`/api/events?since=${lastEventIndex}`);
      if (!res.ok) return;

      const data = await res.json();
      if (data.events && data.events.length > 0) {
        renderEvents(data.events);
        lastEventIndex += data.events.length;
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }, 1000);
}

function renderEvents(events) {
  const eventsLog = document.getElementById('eventsLog');
  const emptyState = eventsLog.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }

  events.forEach((evt) => {
    const item = document.createElement('div');
    item.className = `event-item stage-${evt.stage}`;
    item.innerHTML = `
      <div class="event-header">
        <span class="event-stage">${escapeHtml(evt.stage)}</span>
        <span class="event-time">${escapeHtml(evt.timestamp)}</span>
      </div>
      <div class="event-msg">${escapeHtml(evt.message)}</div>
    `;
    eventsLog.prepend(item);

    // Update stepper based on stage
    handleStageStepper(evt.stage);
  });
}

function handleStageStepper(stage) {
  switch (stage) {
    case 'CALL_INITIATED':
    case 'CALL_QUEUED':
      updateStepper('stepInitiated', true);
      break;
    case 'CALL_ANSWERED':
      updateStepper('stepAnswered', true);
      break;
    case 'OTP_VERIFIED':
      updateStepper('stepOtp', true);
      break;
    case 'OTP_FAILED':
      // flash or mark failed attempt
      const stepOtp = document.getElementById('stepOtp');
      if (stepOtp && !stepOtp.classList.contains('completed')) {
        stepOtp.classList.add('active');
      }
      break;
    case 'LANGUAGE_SELECTED':
      updateStepper('stepLang', true);
      break;
    case 'ACTION_AUDIO_PLAYBACK':
    case 'ACTION_CALL_FORWARD':
    case 'CALL_COMPLETED':
      updateStepper('stepAction', true);
      break;
  }
}

function updateStepper(stepId, isCompleted) {
  const step = document.getElementById(stepId);
  if (!step) return;
  if (isCompleted) {
    step.classList.remove('active');
    step.classList.add('completed');
  } else {
    step.classList.add('active');
  }
}

function resetStepper() {
  ['stepInitiated', 'stepAnswered', 'stepOtp', 'stepLang', 'stepAction'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.className = 'step';
    }
  });
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
