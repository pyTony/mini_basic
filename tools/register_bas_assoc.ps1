# register_bas_assoc.ps1
# Associate .bas files with miniBASIC editor.py and add context-menu entry
# Run as Administrator (right-click → Run with PowerShell as admin)

# ---- CONFIGURE THESE TWO PATHS ----
$EditorScript = "C:\Users\admin\mini_basic\tools\editor.py"   # full path to editor.py
$PythonExe    = "pythonw.exe"   # or full path e.g. "C:\Python312\pythonw.exe"
# -----------------------------------

# Resolve pythonw if only the name is given
if (-not [System.IO.Path]::IsPathRooted($PythonExe)) {
    $PythonExe = (Get-Command $PythonExe -ErrorAction Stop).Source
}

$ProgId = "miniBASIC.Editor"
$MenuText = "Avaa miniBASIC Editorilla"   # Finnish; change if you prefer English

Write-Host "Registering .bas association..."
Write-Host "  Editor : $EditorScript"
Write-Host "  Python : $PythonExe"

# 1. Create the ProgID
New-Item -Path "HKCU:\Software\Classes\$ProgId" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId" -Name "(Default)" -Value "miniBASIC Source File"

# Icon (optional – uses the python icon)
New-Item -Path "HKCU:\Software\Classes\$ProgId\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\DefaultIcon" -Name "(Default)" -Value "$PythonExe,0"

# 2. Open command (double-click)
$OpenCmd = "`"$PythonExe`" `"$EditorScript`" `"%1`""
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\open\command" -Name "(Default)" -Value $OpenCmd

# 3. Context-menu entry (appears alongside "Muokkaa muistiossa")
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\edit" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\edit" -Name "(Default)" -Value $MenuText
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\edit\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\edit\command" -Name "(Default)" -Value $OpenCmd

# 4. Link the .bas extension to our ProgID
New-Item -Path "HKCU:\Software\Classes\.bas" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\.bas" -Name "(Default)" -Value $ProgId

# Also register uppercase .BAS (some tools create it that way)
New-Item -Path "HKCU:\Software\Classes\.BAS" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\.BAS" -Name "(Default)" -Value $ProgId

# 5. Tell Explorer to refresh
$signature = @'
[DllImport("shell32.dll")]
public static extern void SHChangeNotify(int eventId, int flags, IntPtr item1, IntPtr item2);
'@
$type = Add-Type -MemberDefinition $signature -Name ShellNotify -Namespace WinAPI -PassThru
$type::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)   # SHCNE_ASSOCCHANGED

Write-Host ""
Write-Host "Done. .bas files now open with the miniBASIC editor."
Write-Host "Right-click a .bas file → you should see '$MenuText' next to 'Muokkaa muistiossa'."
Write-Host ""
Write-Host "If the menu does not appear immediately, log off/on or restart Explorer."