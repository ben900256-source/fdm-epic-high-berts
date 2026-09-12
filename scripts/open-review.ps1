param([Parameter(Mandatory=$true)][string]$Scene)
$ErrorActionPreference = 'Stop'
$scenePath = (Resolve-Path -LiteralPath $Scene).Path
if ([IO.Path]::GetExtension($scenePath) -ne '.blend') { throw 'Expected a saved Blender scene.' }
$running = @(Get-Process blender -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Sort-Object StartTime -Descending)
if ($running.Count -eq 0) {
    Start-Process -FilePath 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' -ArgumentList ('"' + $scenePath + '"')
    return
}
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class ElfReviewWindow {
    [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int mode);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect r);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
}
'@
$target = $running | Where-Object { $_.MainWindowHandle -eq [ElfReviewWindow]::GetForegroundWindow() } | Select-Object -First 1
if ($null -eq $target) { $target = $running[0] }
$handle = $target.MainWindowHandle
[void][ElfReviewWindow]::ShowWindow($handle, 9)
$shellApp = New-Object -ComObject WScript.Shell
[void]$shellApp.AppActivate($target.Id)
[void][ElfReviewWindow]::SetForegroundWindow($handle)
Start-Sleep -Milliseconds 350
if ([ElfReviewWindow]::GetForegroundWindow() -ne $handle) { throw 'Could not focus the existing Blender window.' }
$bounds = New-Object ElfReviewWindow+Rect
[void][ElfReviewWindow]::GetWindowRect($handle, [ref]$bounds)
[void][ElfReviewWindow]::SetCursorPos(($bounds.Left + [int](($bounds.Right-$bounds.Left)*0.4)), ($bounds.Top + [int](($bounds.Bottom-$bounds.Top)*0.45)))
[System.Windows.Forms.SendKeys]::SendWait('+{F4}')
Start-Sleep -Milliseconds 450
# JSON string syntax safely quotes this Windows path as a Python string.
$pythonPath = ConvertTo-Json -InputObject ($scenePath.Replace('\','/')) -Compress
$command = 'bpy.app.timers.register(lambda: bpy.ops.wm.open_mainfile(filepath=' + $pythonPath + ') and None, first_interval=0.3)'
$clipboardText = Get-Clipboard -Raw -ErrorAction SilentlyContinue
Set-Clipboard -Value $command
try {
    [System.Windows.Forms.SendKeys]::SendWait('^a')
    [System.Windows.Forms.SendKeys]::SendWait('^v')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Seconds 3
} finally {
    if ($null -ne $clipboardText) { Set-Clipboard -Value $clipboardText }
}
$target.Refresh()
if (-not $target.MainWindowTitle.Contains($scenePath)) { throw 'Scene load not confirmed by the Blender window title.' }
[pscustomobject]@{ ProcessId=$target.Id; Reused=$true; Scene=$scenePath }
