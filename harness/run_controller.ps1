param(
  [int]$IntervalSeconds = 30,
  [int]$MaxCyclesPerTick = 10
)

$python = 'C:\Users\LG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$controller = 'D:\GPT-CODECX\KIOM\harness\np_controller.py'
$env:PYTHONPATH = 'D:\GPT-CODECX\KIOM\harness'
$runs = @(
  'D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs\Naringenin__CID_439246__20261010_231827',
  'D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs\5_7-Dihydroxy-8-_3_4_5-trihydroxy-6-_hydroxymeth_20261010_231827'
)

foreach ($run in $runs) {
  $safe = Split-Path $run -Leaf
  $stdout = Join-Path (Split-Path $run -Parent) ("controller_" + $safe + ".stdout.log")
  $stderr = Join-Path (Split-Path $run -Parent) ("controller_" + $safe + ".stderr.log")
  Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @($controller,'--run',$run,'--loop','--interval-seconds',$IntervalSeconds,'--max-cycles',$MaxCyclesPerTick) -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null
}
