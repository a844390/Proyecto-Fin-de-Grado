# --- Interactive Hybrid-aware affinity setter for Core Ultra 7 265KF (20 cores) ---

# Define the physical core layout (P = Performance, E = Efficiency)
$coreLayout = @('P','P','E','E','E','E','P','P','P','P','E','E','E','E','E','E','E','E','P','P')

# Ask for process name
$procName = Read-Host "Enter the process name (e.g. prime95, cinebench, etc.)"

# Find process by name
$procs = Get-Process -Name $procName -ErrorAction SilentlyContinue

if (-not $procs) {
    Write-Host "No process found with name '$procName'. Make sure it's running."
    exit
}

# Handle multiple instances
if ($procs.Count -gt 1) {
    Write-Host "Multiple processes found:"
    $procs | ForEach-Object { Write-Host "PID: $($_.Id)  Name: $($_.ProcessName)" }
    $procId = Read-Host "Enter the PID you want to change"
} else {
    $procId = $procs[0].Id
    Write-Host "Found process '$procName' with PID $procId"
}

$procId = [int]$procId


# --- Display custom core map ---
Write-Host "`n--- Core Map (Physical Layout) ---" -ForegroundColor Cyan
Write-Host "    0:P           1:P" -ForegroundColor Cyan
Write-Host "                2:E 3:E" -ForegroundColor Yellow
Write-Host "                4:E 5:E" -ForegroundColor Yellow
Write-Host "    6:P           7:P" -ForegroundColor Cyan
Write-Host "    8:P           9:P" -ForegroundColor Cyan
Write-Host " 10:E 11:E     14:E 15:E" -ForegroundColor Yellow
Write-Host " 12:E 13:E     16:E 17:E" -ForegroundColor Yellow
Write-Host "    18:P         19:P" -ForegroundColor Cyan
Write-Host "`n(Cyan = P-core, Yellow = E-core)"
Write-Host "Enter core indices separated by commas (e.g. 0,1,7,8,10):"

$coreInput = Read-Host "Cores to enable"

# Parse user selection
$coreIndices = $coreInput -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ }

# Validate
$coreIndices = $coreIndices | Where-Object { $_ -ge 0 -and $_ -lt $coreLayout.Count }
if ($coreIndices.Count -eq 0) {
    Write-Host "No valid cores selected. Exiting."
    exit
}

# Calculate affinity mask
$mask = 0
foreach ($i in $coreIndices) {
    $mask = $mask -bor (1 -shl $i)
}

Write-Host "`nCalculated affinity mask: 0x$("{0:X}" -f $mask)"

# Apply affinity
try {
    $proc = Get-Process -Id $procId -ErrorAction Stop
    $proc.ProcessorAffinity = $mask
    Write-Host "✅ Affinity for PID $procId set to cores: $($coreIndices -join ', ')"
}
catch {
    Write-Host "Error: $($_.Exception.Message)"
}

Read-Host "`nPress Enter to exit"
