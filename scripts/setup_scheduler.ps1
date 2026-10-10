$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonPath = "$ProjectDir\venv\Scripts\python.exe"
$Script = "$ProjectDir\main.py"

if (-not (Test-Path $PythonPath)) {
    Write-Error "Virtual environment not found at $PythonPath. Please run setup first."
    exit 1
}

$ActionCommand = $PythonPath
$ActionArguments = "`"$Script`""

$Action = New-ScheduledTaskAction -Execute $ActionCommand -Argument $ActionArguments -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 10:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "BoletoBot_Daily" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily automation for university invoices (BoletoBot)" -Force

Write-Host "Task 'BoletoBot_Daily' successfully scheduled for 10:00 AM daily." -ForegroundColor Green
