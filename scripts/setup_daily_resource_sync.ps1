$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$TaskName = "P-support-E-expression 每日心理资源更新"

if (-not (Test-Path $PythonExe)) {
    throw "未找到 Python 虚拟环境：$PythonExe"
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "manage.py sync_authoritative_resources --seed-sources" `
    -WorkingDirectory $BackendDir

$Trigger = New-ScheduledTaskTrigger -Daily -At 3:00am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "每天自动抓取 NIMH、WHO、APA 等权威心理健康资源并更新文章库。" `
    -Force

Write-Host "已创建计划任务：$TaskName"
