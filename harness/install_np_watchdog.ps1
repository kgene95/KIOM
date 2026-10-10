param(
    [string]$RunRoot = 'D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs',
    [string]$Python = 'C:\Users\LG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [string]$Harness = 'D:\GPT-CODECX\KIOM\harness\np_harness.py',
    [switch]$Install
)

$taskName = 'KIOM-NP-Harness-Watchdog'
$actionText = "`"$Python`" `"$Harness`" cycle --run `"$RunRoot`" --max-cycles 1"

if (-not $Install) {
    Write-Output "설치하지 않고 확인만 했습니다. 설치하려면 -Install을 명시하십시오."
    Write-Output "Task name: $taskName"
    Write-Output "Action: $actionText"
    exit 0
}

Write-Error '이 스크립트는 아직 run 폴더별 작업 등록 로직이 확정되지 않았습니다. 실제 설치 전 검토가 필요합니다.'
exit 2
