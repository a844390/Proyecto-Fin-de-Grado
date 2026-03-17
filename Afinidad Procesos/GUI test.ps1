Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic

# --- Define layout ---
$coreLayout = @(
    @{ id = 0;  type = 'P'; x = 20;  y = 20 },
    @{ id = 1;  type = 'P'; x = 220; y = 20 },
    @{ id = 2;  type = 'E'; x = 225; y = 70 },
    @{ id = 3;  type = 'E'; x = 305; y = 70 },
    @{ id = 4;  type = 'E'; x = 225; y = 120 },
    @{ id = 5;  type = 'E'; x = 305; y = 120 },
    @{ id = 6;  type = 'P'; x = 20;  y = 170 },
    @{ id = 7;  type = 'P'; x = 220; y = 170 },
    @{ id = 8;  type = 'P'; x = 20;  y = 220 },
    @{ id = 9;  type = 'P'; x = 220; y = 220 },
    @{ id = 10; type = 'E'; x = 25; y = 270 },
    @{ id = 11; type = 'E'; x = 105; y = 270 },
    @{ id = 12; type = 'E'; x = 25; y = 320 },
    @{ id = 13; type = 'E'; x = 105; y = 320 },
    @{ id = 14; type = 'E'; x = 225; y = 270 },
    @{ id = 15; type = 'E'; x = 305; y = 270 },
    @{ id = 16; type = 'E'; x = 225; y = 320 },
    @{ id = 17; type = 'E'; x = 305; y = 320 },
    @{ id = 18; type = 'P'; x = 20;  y = 370 },
    @{ id = 19; type = 'P'; x = 220; y = 370 }
)
$form = New-Object System.Windows.Forms.Form
$form.Text = "Select Cores"
$form.Size = New-Object System.Drawing.Size(420, 560)
$form.StartPosition = "CenterScreen"
$form.BackColor = 'WhiteSmoke'

$selectedCores = @{}

# Helper: set visual style
function Set-CoreStyle($btn, $selected) {
    $coreType = $btn.Tag.Type
    if ($selected) {
        $btn.BackColor = 'PaleGreen'
        $btn.FlatAppearance.BorderColor = 'DarkGreen'
        $btn.FlatAppearance.BorderSize = 3
    } else {
        $btn.BackColor = if ($coreType -eq 'P') { 'LightSkyBlue' } else { 'Khaki' }
        $btn.FlatAppearance.BorderColor = 'Gray'
        $btn.FlatAppearance.BorderSize = 1
    }
    $btn.FlatStyle = 'Flat'
}

# Create buttons
foreach ($core in $coreLayout) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = "$($core.id)`n$($core.type)"
    $btn.Tag = [PSCustomObject]@{ Id = $core.id; Type = $core.type }
    $btn.Font = 'Segoe UI,9'
    $btn.Height = 40
    $btn.Width = if ($core.type -eq 'P') { 160 } else { 70 }
    $btn.Left = $core.x
    $btn.Top  = $core.y
    Set-CoreStyle $btn $false

    $btn.Add_Click({
        $id = $this.Tag.Id
        if ($selectedCores.ContainsKey($id)) {
            $selectedCores.Remove($id)
            Set-CoreStyle $this $false
        } else {
            $selectedCores[$id] = $true
            Set-CoreStyle $this $true
        }
    })

    $form.Controls.Add($btn)
}

# Apply button
$applyBtn = New-Object System.Windows.Forms.Button
$applyBtn.Text = "Apply and Close"
$applyBtn.Width = 360
$applyBtn.Height = 40
$applyBtn.Top = 470
$applyBtn.Left = 20
$applyBtn.BackColor = 'LightGreen'
$applyBtn.Font = 'Segoe UI,10,style=Bold'

$applyBtn.Add_Click({
    $form.Tag = $selectedCores.Keys | Sort-Object
    $form.Close()
})

$form.Controls.Add($applyBtn)

# Show GUI and wait for user
[void]$form.ShowDialog()

# Return the selected cores to the console
$selectedCoresList = $form.Tag
Write-Host "`nSelected cores: $($selectedCoresList -join ', ')"
