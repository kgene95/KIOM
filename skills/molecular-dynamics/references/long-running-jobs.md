# Long-running MD jobs

## Before launch

Record the stage name, input topology and coordinate hashes, MDP/control file, command, working directory, expected duration, log path, output path, checkpoint interval, PID/job ID, and restart command. Confirm that the process is independent of the controlling chat/session before closing that session. If it is foreground or session-dependent, keep its controller open or detach it safely first.

## Completion monitoring

When the user asks for autonomous continuation or a completion alert, create a lightweight heartbeat if the automation facility is available. Select the interval from the recorded expected duration: 30 minutes for a roughly 20-minute–6-hour job, 2 hours for a roughly 6–24-hour job, and 6 hours for a multi-day job. Prefer a scheduler or provider completion callback when available. Inspect only the process/job state, designated log, checkpoint age, and explicit completion/error marker.

Before launching a calculation expected to take hours or days, tell the user the estimated duration, whether it is derived from a prior run on the same machine or is only an estimate, the selected monitoring interval, and that normal progress remains silent. Explain that completion, failure, unexpected stop, or a required decision will generate an alert.

## Productive work while a job runs

Before waiting, inspect the current checkpoint and propose two to four high-value tasks that do not interact with the running process. Favor manuscript/result crosswalks, unresolved scientific-decision memos, figure specifications, provenance and handoff records, production-compute feasibility plans, or post-run analysis specifications.

When the user asks to continue autonomously, start suitable independent work rather than merely polling. Parallel agents may be used only when the user authorizes delegation and each task has separate files and resources. Never use a parallel task to edit active MD inputs/outputs, control the same terminal/GUI, change the running job, or start an additional calculation. Store each result in its own documented project file and summarize it with the active job status.

- Stay silent while the job is healthy and making progress.
- Notify only for normal completion, fatal/LINCS/NaN error, unexpected process stop, stalled checkpoint/log, or a user decision that is genuinely required.
- Do not rerun the calculation, parse the full trajectory, or send routine progress reports during healthy execution.
- Delete the heartbeat after its terminal event.

## Stage chaining

Automatic chaining may connect minimization → NVT → NPT only when each preceding stage has a defined error gate and records its inputs/outputs. Do not automatically begin production MD unless the user explicitly authorizes it. A normal process exit alone is insufficient: check the log for fatal errors, constraint failures, and the intended completion marker.

## After completion

Copy or synchronize the final log, checkpoint, effective run parameters, trajectory, energy file, and QC outputs into the documented project location. When the project uses OneDrive and a local synchronized root exists, write to that local root first and verify the exact copied paths; use the web interface only when local synchronization is unavailable, broken, or requires a remote visibility check. Update the manifest and checkpoint with actual run duration and status before interpretation. Resume from the saved checkpoint rather than restarting completed stages.
