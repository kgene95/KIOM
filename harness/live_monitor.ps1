param(
  [int]$IntervalSeconds = 3
)

$runsRoot = 'D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs'
$runNames = @(
  'Naringenin__CID_439246__20261010_231827',
  '5_7-Dihydroxy-8-_3_4_5-trihydroxy-6-_hydroxymeth_20261010_231827'
)

while ($true) {
  Clear-Host
  Write-Host ('NP HARNESS LIVE MONITOR  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -ForegroundColor Cyan

  foreach ($runName in $runNames) {
    $run = Join-Path $runsRoot $runName
    Write-Host "`n[$runName]" -ForegroundColor Yellow

    $progressPath = Join-Path $run 'analysis_progress.json'
    if (Test-Path $progressPath) {
      try {
        $progress = Get-Content $progressPath -Raw | ConvertFrom-Json
        Write-Host "progress: $($progress.status)  next: $($progress.next_action)"
      } catch { Write-Host 'progress: reading' }
    }

    $ledgerPath = Join-Path $run 'job_ledger.json'
    if (Test-Path $ledgerPath) {
      try {
        $ledger = Get-Content $ledgerPath -Raw | ConvertFrom-Json
        foreach ($provider in @('sea_submission', 'pharmmapper_submission')) {
          $entry = $ledger.$provider
          if ($null -ne $entry) { Write-Host "$provider`: $($entry.status)  job=$($entry.job_id)" }
        }
      } catch { Write-Host 'ledger: reading' }
    }

    $queuePath = Join-Path $run 'work_queue.json'
    if (Test-Path $queuePath) {
      try {
        $queue = Get-Content $queuePath -Raw | ConvertFrom-Json
        foreach ($task in $queue.tasks) { Write-Host ("task {0}: {1}" -f $task.id, $task.status) }
      } catch { Write-Host 'queue: reading' }
    }
  }

  Start-Sleep -Seconds $IntervalSeconds
}
