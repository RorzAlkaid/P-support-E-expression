$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$TaskName = "P-support-E-expression 每日咨询师信息更新"

if (-not (Test-Path $PythonExe)) {
    throw "未找到 Python 虚拟环境：$PythonExe"
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "manage.py sync_authoritative_counselors" `
    -WorkingDirectory $BackendDir

$Trigger = New-ScheduledTaskTrigger -Daily -At 3:20am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "每天自动抓取公开高校心理咨询中心咨询师信息并更新咨询师模块。" `
    -Force

Write-Host "已创建计划任务：$TaskName"
