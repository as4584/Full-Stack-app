📘 EPISTEMOLOGICAL_ENGINEERING.md
Master Documentation for the AI Receptionist Simulation & Self-Improvement System

Version: 1.0
Owner: Lex Santiago
Agent-Class: Epistemological Engineering Agent

🧩 TABLE OF CONTENTS

Overview

Business Scenarios

Audio Simulation Pipeline

Diarization Pipeline

Metrics Engine

Terminal Report Format

Auto-Improvement Trigger

Coding Agent Handoff

Loop Output Format

System Architecture Diagram

Architecture Summary

Module-Level Reference

Task Execution Order

Agent Behavioral Standards

Developer Guide

Changelog

Glossary

Immutable Stability Rule

🧠 1. OVERVIEW

This system is a self-evolving simulation pipeline designed to continuously improve the AI Receptionist using autonomous loops:

Synthetic phone call generation

Text ↔ audio conversion using TTS + Whisper

Full diarization

Quantitative & qualitative analysis

Terminal-based reporting

Automatic code modification

Endless recursive improvement

This methodology is called Epistemological Engineering — a system that evaluates its own knowledge and behavior and improves itself.

📡 2. BUSINESS SCENARIOS

The agent must always generate 3 scenarios:

A: Scheduling request

B: Billing or payment issue

C: Service complaint or escalation

One scenario must require Calendly.

Requirements

6–12 turns

Naturalistic human phrasing

Occasional frustration

AI must remain polite, structured, helpful

🎤 3. AUDIO SIMULATION PIPELINE
Customer turns:

Convert text → TTS using gpt-4o-mini-tts

Save to: /simulation/audio/customer_part_{N}.wav

Whisper STT → /simulation/transcripts/customer_part_{N}.txt

AI turns:

Customer transcript → ChatGPT API

AI response text → TTS

Save AI audio + Whisper STT transcript

This produces a fully synthetic phone call.

🗣️ 4. DIARIZATION & CONVERSATION RECORD

All turns must be merged chronologically with structure:

{
  "turn": N,
  "speaker": "CUSTOMER" | "AI",
  "text": "...",
  "audio_duration_ms": 0,
  "start_timestamp": 0,
  "end_timestamp": 0
}


Saved as:

/simulation/conversation.json

/simulation/conversation.txt

📊 5. PERFORMANCE METRICS ENGINE
Quantitative metrics:

total call length

average AI response delay

max delay

interruption count

overlap %

Whisper accuracy

TTS latency

token usage

cost estimate

Qualitative metrics:

politeness

clarity

emotional tone

customer frustration (0–1)

conversational flow

scenario completeness

Calendly success

UX score (0–100)

Stored internally as: /simulation/metrics.json

🖥️ 6. TERMINAL REPORT FORMAT

The agent MUST print the report directly to terminal (stdout).
Never saved to disk.

Report appears in three structured parts:

(1) Markdown Report

Starts with:

### AI PERFORMANCE REPORT


Contains:

summary

key conversational moments

quantitative metrics

qualitative evaluation

Calendly result

weaknesses

improvement recommendations

(2) ACTION_ITEMS JSON
{
  "severity": "minor" | "moderate" | "critical",
  "actions": [
    {
      "file": "path/to/file.py",
      "change": "specific code modification"
    }
  ]
}

(3) NEXT_AUTOMATION JSON
{
  "auto_trigger": true | false,
  "reason": "analysis summary",
  "severity": "<severity>",
  "execute": "apply_required_fixes"
}


If severity is moderate or critical → auto_trigger MUST be true.

🛠️ 7. AUTO-IMPROVEMENT TRIGGER

If auto_trigger = true, the system must:

read action_items

apply fixes

optimize behavior

improve latency and correctness

Minimal diffs required.

🧰 8. CODING AGENT HANDOFF

Coding agent must:

open each file in action_items

modify the code deterministically

never break existing interfaces

improve system performance

ensure next iteration is better

🔁 9. LOOP OUTPUT FORMAT

After one full cycle:

{
  "status": "pipeline_ready",
  "next_step": "run_simulation",
  "components": [
    "scenario_generator",
    "tts_pipeline",
    "whisper_stt_pipeline",
    "diarizer",
    "metrics_engine",
    "terminal_report_engine",
    "self_improvement_trigger"
  ]
}

🧩 10. SYSTEM ARCHITECTURE DIAGRAM
flowchart TD

A[Epistemological Engineering Agent<br/>Main Controller] --> B1[Scenario Generator]
B1 -->|3 Scenarios| B2[Conversation Script Builder]

B2 --> C1[TTS Module<br/>Text → Customer Audio]
C1 --> C2[Whisper STT<br/>Audio → Customer Text]

C2 --> D1[ChatGPT API<br/>Generate AI Response]
D1 --> D2[TTS Module<br/>AI Text → Audio]
D2 --> D3[Whisper STT<br/>AI Audio → Text]

C2 --> E1
D3 --> E1
E1[Diarization Engine<br/>Merge + Label Speakers] --> E2[Conversation Record]

E2 --> F1[Metrics Engine]
F1 --> F2[Quantitative Metrics]
F1 --> F3[Qualitative Metrics]
F2 & F3 --> F4[metrics.json]

F4 --> G1[Terminal Report Generator]
G1 --> G2[Terminal Output]

G2 --> H1{auto_trigger?}
H1 -->|yes| H2[Self-Improvement Engine]
H2 --> H3[Code Modifications]
H1 -->|no| I1[Stop Loop]

H3 --> A

📌 11. ARCHITECTURE SUMMARY (FOR AGENTS)

Main Agent manages flow

Scenario Generator creates conversations

Audio Simulation runs TTS & Whisper loops

Diarizer merges turns

Metrics Engine evaluates performance

Report Engine outputs markdown + JSON

Self-Improvement Engine applies code changes

📁 12. MODULE-LEVEL REFERENCE
Modules & Responsibilities

Scenario Generator

Create scenarios

Ensure Calendly scenario exists

TTS Pipeline

Convert all CUSTOMER + AI text to audio

Whisper Pipeline

Convert all audio to text

Diarization Engine

Merge transcripts chronologically

Add timestamps

Metrics Engine

Compute quantitative + qualitative metrics

Report Engine

Print markdown report

Print ACTION_ITEMS JSON

Print NEXT_AUTOMATION JSON

Self-Improvement Engine

Apply code modifications

Use minimal diffs

Restart loop

📜 13. TASK EXECUTION ORDER

Agents MUST run tasks in this order:

Generate scenarios

TTS pipeline

Whisper pipeline

Build diarized conversation

Compute metrics

Print terminal report

Severity evaluation

Apply improvements

Restart loop

⚙️ 14. AGENT BEHAVIORAL STANDARDS

Agents MUST:

Follow this spec exactly

Be deterministic

Avoid hallucinating file paths

Produce parseable JSON

Use minimal diffs when editing code

Never invent new modules

Refer to this document when uncertain

🧑‍💻 15. DEVELOPER GUIDE
Setup
pip install -r requirements.txt
python3 run.py

How to Modify

Add new modules under agent/tasks/

Update module definitions in this doc

Update task order if behavior changes

Testing

Run pipeline

Inspect report output

Verify ACTION_ITEMS make sense

🗂️ 16. CHANGELOG

v1.0 – Initial Release

Unified master spec

Added architecture diagram

Created full module references

Specified deterministic task sequence

Defined agent behavioral rules

Added developer instructions

Added glossary

🔤 17. GLOSSARY

Epistemological Engineering — A self-improving knowledge system.
Diarization — Labeling speakers in audio.
AUTO_TRIGGER — Boolean controlling self-improvement.
ACTION_ITEMS — List of required code changes.
NEXT_AUTOMATION — Directive for the coding agent.
Scenario — Synthetic test conversation.

🛡️ 18. IMMUTABLE STABILITY RULE

Agents MUST treat this document as immutable unless Lex explicitly commands updates.

19. MODEL & VERSION COMPATIBILITY RULES

Agents MUST ensure compatibility across all OpenAI and third-party APIs.

General Requirements

Always confirm model availability before execution.

If a model is deprecated, agent MUST select the closest successor (e.g., gpt-4o → gpt-5o-mini).

If Whisper or TTS output fields change, agent MUST adapt mappings automatically.

All timestamps MUST be normalized to milliseconds regardless of source.

Error Handling

If an API model returns an error:

Retry the same call up to 2 times.

If still failing, log the error in the PERFORMANCE REPORT.

Mark severity as "critical".

Trigger auto-improvement.

Provider Flexibility

If alternative providers (ElevenLabs, deepgram, faster-whisper, etc.) are available, the agent may substitute only if it preserves existing output formats.

This rule ensures long-term stability as APIs evolve.

20. FAILSAFE & ROLLBACK RULES

If any self-applied code modification or simulation step causes failure, the agent MUST follow this workflow:

Failure Conditions

Runtime errors

Invalid or malformed JSON

Missing fields in reports

Broken file paths

Simulation stalls

Metrics missing or zeroed

TTS/Whisper pipeline output is unusable

Rollback Procedure

Upon detecting failure:

Restore the last known working version of each modified file.

Log the failure in the terminal report.

Set severity to "critical".

Trigger auto-improvement with a different strategy than the attempted patch.

Never repeat the exact same failing patch twice.

This prevents the system from degrading over time.

21. DATA RETENTION & LOGGING POLICY

To avoid disk bloat and ensure clean simulation cycles:

Retain

The latest simulation folder

The last 3 successful conversation logs

The last applied diff produced by self-improvement

Auto-Delete

Simulations older than 3 runs

Temporary Whisper artifacts

Any stale JSON, wav, or partial data files

Corrupted simulation output

Logging Requirements

Errors → /simulation/logs/errors.log

Performance insights → /simulation/logs/performance.log

Logs MUST not include any sensitive PII

Logs MUST remain under 5MB total

Ensures the pipeline stays efficient and storage-safe.

22. SIMULATION VARIABILITY RULES

To prevent the model from generating the same repetitive conversations, each simulation cycle MUST vary in the following ways:

Required Variation Dimensions

Customer emotion (neutral, annoyed, confused, rushed)

Speaking pace (slow, normal, rapid)

Noise profile (quiet office, mild background noise)

Persona (different names, ages, gender-neutral options)

Appointment times & dates

Billing amounts & case descriptions

Complaint severity (mild, moderate, urgent)

Calendly use-case in different contexts

Prohibition

No two consecutive simulations may have identical customer lines

No scenario may be reused verbatim

This provides diversity and prevents overfitting to a single call template.

23. PERFORMANCE TARGETS

The system MUST evaluate itself against fixed performance thresholds.

Target Metrics

Average AI response delay < 350 ms

Maximum delay < 700 ms

Whisper accuracy ≥ 95%

TTS generation latency < 200 ms

Interruption rate < 5%

Calendly success rate = 100%

User Experience Score ≥ 85 / 100

Failure Handling

If any target is missed:

Severity MUST be "moderate" or "critical"

auto_trigger MUST be set to true

Self-improvement MUST attempt optimization in next cycle

This provides clear quantitative objectives for the system to converge toward.

24. ENVIRONMENT & EXECUTION RULES

To maintain deterministic behavior across local machines, servers, and Antigravity:

Runtime Requirements

Python 3.10+

UTF-8 encoding for all file reads/writes

All timestamps in milliseconds

All numerical metrics must be float or int (no strings)

Execution Rules

Agent MUST run each task synchronously in the defined order

Agent MUST NOT parallelize tasks unless explicitly instructed

Agent MUST NOT modify environment variables unless required

Agent MUST ensure /simulation/ exists before writing

Hardware Flexibility

The system MUST function regardless of:

CPU vs GPU

1–32 GB RAM

Cloud VM or local machine

If system resources are low:

Agent MUST reduce scenario complexity

Agent MUST reduce background noise variation

Agent MUST keep output format identical

25. FILE & DIRECTORY STRUCTURE REQUIREMENTS

To avoid confusion and guarantee stable file paths:

Simulations Folder Structure
/simulation/
    audio/
    transcripts/
    logs/
    conversation.json
    conversation.txt
    metrics.json

Audio Naming Convention
customer_part_{N}.wav
ai_part_{N}.wav

Transcript Naming Convention
customer_part_{N}.txt
ai_part_{N}.txt

Logging Rules

Errors → logs/errors.log

Performance → logs/performance.log

Logs MUST append, never overwrite

File Write Safety

If a file fails to write:

Retry twice

If still failing, mark severity as "critical"

Trigger rollback

26. AGENT-TO-AGENT COMMUNICATION RULES

If multiple agents (Antigravity, AgentKit, Coding Agent) are active:

Rules

Agents MUST communicate through structured JSON

Agents MUST NOT rely on natural language alone

Agents MUST clearly identify themselves in logs

Agents MUST maintain backward compatibility

Agents MUST NOT override each other’s memory states

Agents MUST always read the latest terminal output before acting

Handoff Format

Every handoff MUST use:

{
  "task": "<task_name>",
  "input": {...},
  "expected_output": {...}
}


This eliminates ambiguity.

27. TESTING & VERIFICATION RULES

To maintain reliability:

Simulation MUST pass these checks before improvement:

All transcripts are present

All audio files exist and have non-zero duration

Metrics JSON is fully populated

No JSON parsing errors

Conversation has matching turn counts

Calendly scenario executed when required

Verification Failure

If any check fails:

Mark severity = "critical"

Trigger rollback

Flag error in report

Auto-trigger self-improvement

28. ADVANCED ERROR CLASSIFICATION

Errors MUST be classified into three levels:

Level 1 — Minor

Slight delays above threshold

Non-critical formatting issues

Minor Whisper inaccuracies

Run continues normally

Level 2 — Moderate

Sustained latency issues

Repeated transcription drift

AI responses mismatched with intent

Missing fields in metrics

auto_trigger = true

Level 3 — Critical

Crash

Incorrect file writes

Invalid JSON

Broken directory structure

Missing files

TTS/Whisper failures

auto_trigger = true

mandatory rollback

This classification guides auto-improvement.

29. BENCHMARKING GUIDE

The system must assess long-term improvement, not just per-run quality.

Monthly Benchmarking Requirements

Agents MUST calculate:

Average UX Score (30-run window)

Trending AI Response Delay (should decrease)

Error Rate Frequency

Scenario Variety Diversity Index (SVDI)

Percentage of successful Calendly use-cases

Mean Whisper Accuracy

Benchmarks MUST be printed into a file:
/simulation/logs/benchmarks.log

Improvement Threshold

If average performance declines:

Severity = "critical"

Self-improvement MUST attempt structural optimization

30. FUTURE-PROOFING & EXTENSIBILITY RULES

Agents MUST ensure the system is easy to extend.

Extensibility Requirements

All modules MUST accept optional arguments

All task functions MUST support future keyword arguments (**kwargs)

No module may hardcode file paths; use a central config

New providers (e.g., ElevenLabs, Google TTS) MUST integrate without rewriting core logic

System MUST support additional modalities (video, images)

Future-Proof Scenarios

Scenarios must be flexible to support:

multi-party calls

multi-language calls

long-form calls (5–10 minutes)

emotional escalation modeling

Agents MUST NOT limit future simulation complexity.

🚫 PROHIBITED BEHAVIORS (CRITICAL SECTION)

Agents MUST NEVER:

invent tasks or modules not defined in this spec

hallucinate file paths

rewrite this spec unless Lex commands it

skip tasks in the sequence

reorder tasks

output broken or partial JSON

override or erase logs without instruction

create infinite loops

use randomness without documenting seed

generate PII

hardcode timestamps

ignore an error condition

Violating any of these rules MUST set:

severity = "critical"
auto_trigger = true

🧪 TEST CASES (MANDATORY)

These verify system reliability.

Test Case 1 — Basic Flow

All modules run successfully

Metrics populated

No errors

Severity = "minor" or "none"

Test Case 2 — Whisper Failure

Simulate missing transcript file:

Whisper should retry

If still fails → severity = "critical"

Rollback triggered

Test Case 3 — Latency Spike

Inject artificial delay:

AI response > 700ms

severity = "moderate"

auto_trigger = true

Improvement required

Test Case 4 — Broken JSON

Break metrics.json:

Parsing fails

severity = "critical"

rollback

Test Case 5 — Missing Calendly Execution

If Calendly scenario exists but isn’t executed:

severity = "moderate"

auto_trigger = true

📊 BENCHMARKING GUIDE (MANDATORY)

This section teaches the agent how to evaluate long-term improvement.

Metrics to Track Over Time

Average response delay

Whisper accuracy rates

UX Score trending

Scenario complexity growth

Variety and non-repetition rate

Error classification frequency

Average cost per simulation

Benchmark Structure Example
{
  "timestamp": 1712072398841,
  "avg_ux_score_30_runs": 87,
  "avg_latency_ms": 284,
  "whisper_accuracy": 96.4,
  "error_rate": 3.1,
  "scenario_diversity": 0.82
}

Benchmark Storage

All benchmark entries MUST be appended to:

/simulation/logs/benchmarks.log

Decline Detection

If UX score drops >10% over any 10-run window:

severity = "critical"

auto_trigger = true

attempt structural optimization

This is the source of truth for the entire system.