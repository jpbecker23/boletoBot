$ProjectDir = Get-Location
$PythonPath = "$ProjectDir\venv\Scripts\python.exe"
$Script1 = "$ProjectDir\baixar_boletos.py"
$Script2 = "$ProjectDir\enviar_boletos.py"

if (-not (Test-Path $PythonPath)) {
    Write-Error "Virtual environment not found at $PythonPath. Please run setup first."
    exit 1
}

$ActionCommand = "cmd.exe"
$ActionArguments = "/c `"$PythonPath`" `"$Script1`" && `"$PythonPath`" `"$Script2`""

$Action = New-ScheduledTaskAction -Execute $ActionCommand -Argument $ActionArguments -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 10:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "BoletoBot_Daily" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily automation for university invoices (BoletoBot)" -Force

Write-Host "Task 'BoletoBot_Daily' successfully scheduled for 10:00 AM daily." -ForegroundColor Green
