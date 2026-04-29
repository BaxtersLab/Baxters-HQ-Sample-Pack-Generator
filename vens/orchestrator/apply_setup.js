/**
 * ============================================================
 * VENS SETUP APPLIER v1.0
 * ============================================================
 * 
 * Reads the completed SETUP_WIZARD.txt and distributes the
 * user's answers into the correct Vens files.
 * 
 * Usage:  node apply_setup.js
 * 
 * This script writes to:
 *   - /vens/constitution/user/PROJECT_SOURCE_PATH.txt
 *   - /vens/constitution/user/MAIN_GOAL.txt
 *   - /vens/constitution/user/TRIGGER_WORKFLOW.txt
 *   - /vens/tasks/pending.json
 *   - /vens/state/active_agent.txt
 * ============================================================
 */

const fs = require('fs');
const path = require('path');

const VENS_ROOT = path.resolve(__dirname, '..');
const WIZARD_PATH = path.join(__dirname, 'SETUP_WIZARD.txt');

// ============================================================
// PARSE WIZARD FILE
// ============================================================

function parseWizard() {
  if (!fs.existsSync(WIZARD_PATH)) {
    console.error('ERROR: SETUP_WIZARD.txt not found.');
    process.exit(1);
  }

  const content = fs.readFileSync(WIZARD_PATH, 'utf8');
  const values = {};

  const lines = content.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('#') || trimmed === '') continue;

    const eqIndex = trimmed.indexOf('=');
    if (eqIndex === -1) continue;

    const key = trimmed.substring(0, eqIndex).trim();
    const value = trimmed.substring(eqIndex + 1).trim();
    values[key] = value;
  }

  return values;
}

// ============================================================
// VALIDATION
// ============================================================

function validate(values) {
  const required = [
    'PROJECT_NAME', 'SOURCE_PATH', 'PRIMARY_OBJECTIVE',
    'TASK_DESCRIPTION', 'TASK_PRIORITY', 'ASSIGN_TO', 'TRIGGER_COMMAND'
  ];

  const missing = [];
  for (const key of required) {
    if (!values[key] || values[key].startsWith('(FILL IN')) {
      missing.push(key);
    }
  }

  if (missing.length > 0) {
    console.error('\n  ❌ The following fields are still blank or unfilled:\n');
    missing.forEach(k => console.error(`     - ${k}`));
    console.error('\n  Please fill in SETUP_WIZARD.txt and try again.\n');
    process.exit(1);
  }

  return true;
}

// ============================================================
// APPLY TO VENS FILES
// ============================================================

function apply(v) {
  const timestamp = new Date().toISOString();

  // 1. PROJECT_SOURCE_PATH.txt
  const projectPath = `# PROJECT_SOURCE_PATH.txt\n\nPROJECT NAME: ${v.PROJECT_NAME}\nSOURCE PATH: ${v.SOURCE_PATH}\n`;
  fs.writeFileSync(
    path.join(VENS_ROOT, 'constitution', 'user', 'PROJECT_SOURCE_PATH.txt'),
    projectPath, 'utf8'
  );
  console.log('  ✅ PROJECT_SOURCE_PATH.txt updated');

  // 2. MAIN_GOAL.txt
  const constraints = v.NON_NEGOTIABLE_CONSTRAINTS || '(none specified)';
  const criteria = v.SUCCESS_CRITERIA || '(none specified)';
  const mainGoal = `# MAIN_GOAL.txt

============================================================
1. PRIMARY OBJECTIVE
============================================================
${v.PRIMARY_OBJECTIVE}

============================================================
2. NON-NEGOTIABLE CONSTRAINTS
============================================================
${constraints}

============================================================
3. SUCCESS CRITERIA
============================================================
${criteria}

============================================================
4. HUMAN SUPREMACY NOTE
============================================================
The human operator (Sage) is the sole authority over this goal.
Agents must never reinterpret, expand, or alter the goal.
Agents must only execute toward the goal as written.

END OF MAIN_GOAL.txt
`;
  fs.writeFileSync(
    path.join(VENS_ROOT, 'constitution', 'user', 'MAIN_GOAL.txt'),
    mainGoal, 'utf8'
  );
  console.log('  ✅ MAIN_GOAL.txt updated');

  // 3. pending.json
  const task = [{
    task_id: 'TASK-001',
    description: v.TASK_DESCRIPTION,
    assigned_to: v.ASSIGN_TO.toUpperCase(),
    priority: parseInt(v.TASK_PRIORITY) || 3,
    status: 'PENDING',
    created_at: timestamp,
    updated_at: timestamp,
    dependencies: [],
    notes: ''
  }];
  fs.writeFileSync(
    path.join(VENS_ROOT, 'tasks', 'pending.json'),
    JSON.stringify(task, null, 2), 'utf8'
  );
  console.log('  ✅ pending.json updated with TASK-001');

  // 4. TRIGGER_WORKFLOW.txt
  const triggerContent = `${v.TRIGGER_COMMAND}\n`;
  fs.writeFileSync(
    path.join(VENS_ROOT, 'constitution', 'user', 'TRIGGER_WORKFLOW.txt'),
    triggerContent, 'utf8'
  );
  console.log(`  ✅ TRIGGER_WORKFLOW.txt set to: ${v.TRIGGER_COMMAND}`);

  // 5. active_agent.txt
  const firstAgent = v.ASSIGN_TO.toUpperCase();
  fs.writeFileSync(
    path.join(VENS_ROOT, 'state', 'active_agent.txt'),
    firstAgent, 'utf8'
  );
  console.log(`  ✅ active_agent.txt set to: ${firstAgent}`);
}

// ============================================================
// MAIN
// ============================================================

function main() {
  console.log('\n  ╔══════════════════════════════════════════╗');
  console.log('  ║      VENS SETUP APPLIER v1.0             ║');
  console.log('  ╚══════════════════════════════════════════╝\n');

  const values = parseWizard();
  validate(values);

  console.log('  Applying your setup to the Vens system...\n');
  apply(values);

  console.log('\n  ══════════════════════════════════════════');
  console.log('  ✅ SETUP COMPLETE!');
  console.log('  ══════════════════════════════════════════');
  console.log(`\n  Project:  ${values.PROJECT_NAME}`);
  console.log(`  Agent:    ${values.ASSIGN_TO.toUpperCase()}`);
  console.log(`  Trigger:  ${values.TRIGGER_COMMAND}`);
  console.log('\n  The orchestrator will now start...\n');
}

main();
