// Groups the flat SSE log stream into per-step sections, using the
// "STEP N: ..." header every pipeline step script already prints as the
// boundary marker. No backend change is required for this — every step
// script has always printed this header, so it's a reliable signal.

const TIMESTAMP_RE = /^\[(\d{2}):(\d{2}):(\d{2})\]\s*/;
const STEP_HEADER_RE = /^STEP\s/i;
const RULE_RE = /^=+$/;

// Which STEPS[] id a parsed group belongs to, matched against the group's
// title (the raw "STEP ..." header line, timestamp stripped).
export const STEP_MATCHERS = [
  { id: 'step1_extract_audio', re: /^STEP\s+1:/i },
  { id: 'step2_transcribe_diarization', re: /^STEP\s+2:/i },
  { id: 'step2b_gender_confirm', re: /^STEP\s+2b:/i },
  { id: 'step3_translation', re: /^STEP\s+3:/i },
  { id: 'step4_setup', re: /^STEP\s+4\s+Setup:/i },
  { id: 'step4_genvoice_complete', re: /^STEP\s+4\s+Gen:/i },
  { id: 'step5_assembly', re: /^STEP\s+5:/i },
];

export function stripTimestamp(line) {
  return line.replace(TIMESTAMP_RE, '');
}

export function groupLogs(logs) {
  const groups = [];
  let current = { key: 'preamble', title: 'Session', lines: [] };

  for (const line of logs) {
    const message = stripTimestamp(line);
    if (STEP_HEADER_RE.test(message)) {
      // Pull a trailing lone "====" rule out of the previous group so it
      // stays attached to the header it visually belongs to.
      let carried = null;
      if (current.lines.length && RULE_RE.test(stripTimestamp(current.lines[current.lines.length - 1]).trim())) {
        carried = current.lines.pop();
      }
      if (current.lines.length) groups.push(current);
      current = { key: `step-${groups.length}`, title: message.trim(), lines: [] };
      if (carried) current.lines.push(carried);
    }
    current.lines.push(line);
  }
  if (current.lines.length) groups.push(current);
  return groups;
}

export function classifyGroup(lines, isLast) {
  const joined = lines.join('\n');
  if (/❌|failed|error/i.test(joined)) return 'error';
  if (/✅|🎉|SUCCESS|Complete!/i.test(joined)) return 'ok';
  return isLast ? 'running' : 'ok';
}

// Last meaningful (non-rule, non-empty) line in a group, used as the
// live "what's it doing right now" caption for a running step.
function lastDetailLine(lines) {
  for (let i = lines.length - 1; i >= 0; i--) {
    const msg = stripTimestamp(lines[i]).trim();
    if (msg && !RULE_RE.test(msg) && !STEP_HEADER_RE.test(msg)) return msg;
  }
  return '';
}

function parseSeconds(line) {
  const m = line.match(TIMESTAMP_RE);
  if (!m) return null;
  return (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]);
}

function groupDurationLabel(lines) {
  const start = parseSeconds(lines[0]);
  const end = parseSeconds(lines[lines.length - 1]);
  if (start == null || end == null) return '';
  let delta = end - start;
  if (delta < 0) delta += 86400; // midnight rollover
  if (delta < 60) return `${delta}s`;
  return `${Math.floor(delta / 60)}m ${delta % 60}s`;
}

// Derives {status, detail, time} for every step in STEP_MATCHERS from the
// raw log stream. Steps with no matching group yet are 'pending'.
export function deriveStepStates(logs) {
  const groups = groupLogs(logs);
  const states = {};
  STEP_MATCHERS.forEach(({ id }) => {
    states[id] = { status: 'pending', detail: '', time: '' };
  });

  groups.forEach((group, idx) => {
    const matcher = STEP_MATCHERS.find((m) => m.re.test(group.title));
    if (!matcher) return;
    const isLast = idx === groups.length - 1;
    const status = classifyGroup(group.lines, isLast);
    states[matcher.id] = {
      status,
      detail: status === 'running' ? lastDetailLine(group.lines) : '',
      time: status !== 'running' ? groupDurationLabel(group.lines) : '',
    };
  });

  return states;
}
