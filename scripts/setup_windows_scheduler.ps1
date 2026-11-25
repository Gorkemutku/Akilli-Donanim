# Windows Görev Zamanlayıcısı (Task Scheduler) Otomasyon Kurulum Betiği
# KDS Günlük Canlı Veri Senkronizasyonunu her gün saat 09:00'da çalışacak şekilde kurar.

$TaskName = "KDS_Daily_Hardware_Sync"
$ScriptDir = Split-Path -Parent $PSScriptRoot
$BatPath = Join-Path $PSScriptRoot "daily_sync.bat"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  KDS Windows Görev Zamanlayıcısı Kurulumu" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Görev Adı: $TaskName"
Write-Host "Çalıştırılacak Dosya: $BatPath"
Write-Host "Zamanlama: Her gün 09:00"

$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "KDS Donanım ve Cihaz Seçim Sistemi Günlük Canlı Veri Senkronizasyonu"
    Write-Host "[+] Başarılı! '$TaskName' görevi Windows Görev Zamanlayıcısı'na kaydedildi." -ForegroundColor Green
    Write-Host "    Test etmek için: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
} catch {
    Write-Host "[-] Hata oluştu: $_" -ForegroundColor Red
}
