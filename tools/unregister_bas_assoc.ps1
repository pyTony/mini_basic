# unregister_bas_assoc.ps1
# Removes the Mini-BASIC .bas / .bbc file association registered by register_bas_assoc.ps1

$ErrorActionPreference = 'Stop'

# Remove the ProgID and its verbs
Remove-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram' -Recurse -Force -ErrorAction SilentlyContinue

# Remove the extension mappings
Remove-Item -Path 'HKCU:\Software\Classes\.bas' -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path 'HKCU:\Software\Classes\.bbc' -Recurse -Force -ErrorAction SilentlyContinue

# Tell Explorer that associations have changed
$signature = @'
[DllImport("shell32.dll")]
public static extern void SHChangeNotify(int eventId, int flags, IntPtr item1, IntPtr item2);
'@
$type = Add-Type -MemberDefinition $signature -Name 'ShellNotify' -Namespace 'WinAPI' -PassThru
$type::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)   # SHCNE_ASSOCCHANGED

Write-Host 'Unregistered .bas / .bbc association.'
Write-Host 'You may need to restart Explorer or log off/on for the change to appear everywhere.'