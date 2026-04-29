/**
 * ============================================================
 * VENS ORCHESTRATOR v1.0
 * ============================================================
 * 
 * A zero-dependency file watcher that monitors the Vens system
 * and dispatches Windows desktop notifications when agent turns
 * change. This is the execution spine of the Vens protocol.
 * 
 * Usage:  node orchestrator.js
 * Stop:   Ctrl+C
 * 
 * This script is READ-ONLY. It never writes to any Vens file.
 * ============================================================
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ============================================================
// CONFIGURATION
// ============================================================

const VENS_ROOT = path.resolve(__dirname, '..');
const PATHS = {
  activeAgent:     path.join(VENS_ROOT, 'state', 'active_agent.txt'),
  triggerWorkflow: path.join(VENS_ROOT, 'constitution', 'user', 'TRIGGER_WORKFLOW.txt'),
  lastAction:      path.join(VENS_ROOT, 'state', 'last_action.md'),
  toHuman:         path.join(VENS_ROOT, 'messages', 'to_human.md'),
  toAntigravity:   path.join(VENS_ROOT, 'messages', 'to_antigravity.md'),
  toCopilot:       path.join(VENS_ROOT, 'messages', 'to_copilot.md'),
};

const POLL_INTERVAL_MS = 2000; // Check files every 2 seconds

// ============================================================
// STATE
// ============================================================

let currentAgent = '';
let systemStatus = 'INITIALIZING';
let eventLog = [];
const MAX_LOG_ENTRIES = 15;

// ============================================================
// NOTIFICATION (Windows PowerShell)
// ============================================================

function notify(title, message) {
  const escapedTitle = title.replace(/'/g, "''");
  const escapedMessage = message.replace(/'/g, "''");

  // Try BurntToast first, fall back to basic balloon notification
  const script = `
    $ErrorActionPreference = 'SilentlyContinue'
    try {
      if (Get-Module -ListAvailable -Name BurntToast) {
        Import-Module BurntToast
        New-BurntToastNotification -Text '${escapedTitle}', '${escapedMessage}'
      } else {
        Add-Type -AssemblyName System.Windows.Forms
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Information
        $n.Visible = $true
        $n.ShowBalloonTip(5000, '${escapedTitle}', '${escapedMessage}', 'Info')
        Start-Sleep -Seconds 6
        $n.Dispose()
      }
    } catch {
      Write-Host "Notification: ${escapedTitle} - ${escapedMessage}"
    }
  `;

  try {
    execSync(`powershell -NoProfile -Command "${script.replace(/\n/g, ' ')}"`, {
      stdio: 'ignore',
      timeout: 10000
    });
  } catch (e) {
    // Notification failed silently — console output is the fallback
  }
}

// ============================================================
// AGENT DISPATCH MESSAGES
// ============================================================

const AGENT_MESSAGES = {
  ANTIGRAVITY: {
    title: '🚀 ANTIGRAVITY\'s Turn',
    message: 'Go to your Antigravity chat and tell it: "Read /vens/messages/to_antigravity.md and begin your cycle."',
    color: '\x1b[35m', // Magenta
  },
  COPILOT: {
    title: '🤖 COPILOT\'s Turn',
    message: 'Go to VS Code Copilot and tell it: "Read /vens/messages/to_copilot.md and execute the plan."',
    color: '\x1b[36m', // Cyan
  },
  HUMAN: {
    title: '👤 YOUR Turn (Human)',
    message: 'Agent attention is needed. Check /vens/messages/to_human.md and /vens/state/last_action.md.',
    color: '\x1b[33m', // Yellow
  },
  IDLE: {
    title: '💤 System Idle',
    message: 'No agent is active. Write a trigger to TRIGGER_WORKFLOW.txt to begin.',
    color: '\x1b[90m', // Gray
  },
};

// ============================================================
// FILE READING UTILITIES
// ============================================================

function readFileSafe(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8').trim();
  } catch (e) {
    return '';
  }
}

function getFileModTime(filePath) {
  try {
    return fs.statSync(filePath).mtimeMs;
  } catch (e) {
    return 0;
  }
}

// ============================================================
// EVENT LOGGING
// ============================================================

function logEvent(message) {
  const timestamp = new Date().toLocaleTimeString();
  const entry = `[${timestamp}] ${message}`;
  eventLog.unshift(entry);
  if (eventLog.length > MAX_LOG_ENTRIES) {
    eventLog = eventLog.slice(0, MAX_LOG_ENTRIES);
  }
}

// ============================================================
// CONSOLE DASHBOARD
// ============================================================

function renderDashboard() {
  const reset = '\x1b[0m';
  const bold = '\x1b[1m';
  const dim = '\x1b[2m';
  const green = '\x1b[32m';
  const red = '\x1b[31m';
  const yellow = '\x1b[33m';
  const cyan = '\x1b[36m';
  const magenta = '\x1b[35m';
  const white = '\x1b[37m';

  const agentInfo = AGENT_MESSAGES[currentAgent] || AGENT_MESSAGES.IDLE;
  const statusColor = systemStatus === 'ACTIVE' ? green :
                       systemStatus === 'HALTED' ? red :
                       systemStatus === 'IDLE' ? dim : yellow;

  // Clear screen
  process.stdout.write('\x1b[2J\x1b[H');

  console.log(`${bold}${cyan}╔══════════════════════════════════════════════════════════╗${reset}`);
  console.log(`${bold}${cyan}║          VENS ORCHESTRATOR v1.0  —  Live Dashboard       ║${reset}`);
  console.log(`${bold}${cyan}╚══════════════════════════════════════════════════════════╝${reset}`);
  console.log();
  console.log(`  ${bold}System Status:${reset}  ${statusColor}${bold}${systemStatus}${reset}`);
  console.log(`  ${bold}Active Agent:${reset}   ${agentInfo.color}${bold}${currentAgent || 'NONE'}${reset}`);
  console.log(`  ${bold}Polling:${reset}        Every ${POLL_INTERVAL_MS / 1000}s`);
  console.log();

  if (currentAgent && AGENT_MESSAGES[currentAgent]) {
    console.log(`${bold}${white}  ┌─ Action Required ─────────────────────────────────────┐${reset}`);
    console.log(`${white}  │ ${agentInfo.message}${reset}`);
    console.log(`${bold}${white}  └────────────────────────────────────────────────────────┘${reset}`);
    console.log();
  }

  console.log(`${bold}  Recent Events:${reset}`);
  console.log(`  ${dim}${'─'.repeat(56)}${reset}`);
  if (eventLog.length === 0) {
    console.log(`  ${dim}  No events yet. Watching for changes...${reset}`);
  } else {
    eventLog.forEach(entry => {
      console.log(`  ${dim}  ${entry}${reset}`);
    });
  }
  console.log(`  ${dim}${'─'.repeat(56)}${reset}`);
  console.log();
  console.log(`  ${dim}Press Ctrl+C to stop the orchestrator.${reset}`);
}

// ============================================================
// FILE WATCHERS (Polling-based for reliability on Windows)
// ============================================================

let lastAgentModTime = 0;
let lastTriggerModTime = 0;
let lastToHumanModTime = 0;

function checkActiveAgent() {
  const modTime = getFileModTime(PATHS.activeAgent);
  if (modTime > lastAgentModTime) {
    lastAgentModTime = modTime;

    const newAgent = readFileSafe(PATHS.activeAgent).toUpperCase();
    if (newAgent && newAgent !== currentAgent) {
      const previousAgent = currentAgent;
      currentAgent = newAgent;

      if (previousAgent) {
        logEvent(`Turn changed: ${previousAgent} → ${currentAgent}`);
      } else {
        logEvent(`Initial state: ${currentAgent}`);
      }

      const agentInfo = AGENT_MESSAGES[currentAgent];
      if (agentInfo) {
        systemStatus = (currentAgent === 'IDLE') ? 'IDLE' : 'ACTIVE';
        notify(agentInfo.title, agentInfo.message);
      } else {
        logEvent(`Unknown agent value: "${currentAgent}"`);
      }

      renderDashboard();
    }
  }
}

function checkTriggerWorkflow() {
  const modTime = getFileModTime(PATHS.triggerWorkflow);
  if (modTime > lastTriggerModTime) {
    lastTriggerModTime = modTime;

    const content = readFileSafe(PATHS.triggerWorkflow);
    // Look for HALT or START commands in the file content
    const lines = content.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    
    for (const line of lines) {
      if (line === 'HALT') {
        systemStatus = 'HALTED';
        logEvent('TRIGGER: HALT received — system halted');
        notify('⛔ VENS HALTED', 'HALT command received. All agents must stop.');
        renderDashboard();
        return;
      }
      if (line === 'START' || line.startsWith('BEGIN MODULE') || line === 'EXECUTE MAIN_GOAL') {
        systemStatus = 'ACTIVE';
        logEvent(`TRIGGER: ${line}`);
        notify('▶️ VENS ACTIVATED', `Trigger received: ${line}`);
        renderDashboard();
        return;
      }
    }
  }
}

function checkHumanMessages() {
  const modTime = getFileModTime(PATHS.toHuman);
  if (modTime > lastToHumanModTime && lastToHumanModTime > 0) {
    lastToHumanModTime = modTime;

    const content = readFileSafe(PATHS.toHuman);
    if (content.length > 0) {
      logEvent('New message in to_human.md');
      notify('📬 Message For You', 'An agent has written to /vens/messages/to_human.md');
      renderDashboard();
    }
  } else if (lastToHumanModTime === 0) {
    lastToHumanModTime = modTime;
  }
}

// ============================================================
// MAIN LOOP
// ============================================================

function main() {
  // Verify Vens structure exists
  if (!fs.existsSync(PATHS.activeAgent)) {
    console.error(`ERROR: Cannot find ${PATHS.activeAgent}`);
    console.error('Make sure the orchestrator is inside /vens/orchestrator/');
    process.exit(1);
  }

  // Initial read
  currentAgent = readFileSafe(PATHS.activeAgent).toUpperCase() || 'IDLE';
  lastAgentModTime = getFileModTime(PATHS.activeAgent);
  lastTriggerModTime = getFileModTime(PATHS.triggerWorkflow);
  lastToHumanModTime = getFileModTime(PATHS.toHuman);

  systemStatus = (currentAgent === 'IDLE') ? 'IDLE' : 'ACTIVE';

  logEvent('Orchestrator started');
  logEvent(`Initial agent: ${currentAgent}`);
  renderDashboard();

  // Polling loop
  setInterval(() => {
    checkActiveAgent();
    checkTriggerWorkflow();
    checkHumanMessages();
  }, POLL_INTERVAL_MS);
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n  Orchestrator stopped. Vens system is now unmonitored.\n');
  process.exit(0);
});

main();
