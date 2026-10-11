param([int]$IntervalSeconds = 60, [int]$StaleAfterSeconds = 300)
$python = 'C:\Users\LG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$supervisor = 'D:\GPT-CODECX\KIOM\harness\supervisor.py'
$workspace = 'D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs'
$log = Join-Path $workspace 'supervisor.log'
Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @($supervisor,'--workspace',$workspace,'--interval-seconds',$IntervalSeconds,'--stale-after-seconds',$StaleAfterSeconds) -RedirectStandardOutput $log -RedirectStandardError (Join-Path $workspace 'supervisor.error.log') | Out-Null

