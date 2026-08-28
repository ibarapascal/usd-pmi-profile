# E2 第二开源链批转换（pc-b, Windows）：STEP -> Mayo 0.10.0 (mayo-conv) -> glTF(.glb) -> guc 0.5 (USD 25.11) -> .usdc
# 环境：C:\e2-mayo\{mayo\Mayo-0.10.0-win64-binaries\mayo-conv.exe, bin\guc.exe, lib=USD25.11 prebuilt(pablode/USD v25.11-ci-release)}
# 输入：C:\e2-mayo\step\*.stp（NIST MBE PMI 17 件）；输出：C:\e2-mayo\out\*.glb / *.usdc；日志：C:\e2-mayo\out\e2_batch.log
# 用法：powershell -ExecutionPolicy Bypass -File 25_e2_pcb_batch.ps1
$ErrorActionPreference = "Continue"
$env:PATH = "C:\e2-mayo\bin;C:\e2-mayo\lib;" + $env:PATH
$mayo = "C:\e2-mayo\mayo\Mayo-0.10.0-win64-binaries\mayo-conv.exe"
$guc  = "C:\e2-mayo\bin\guc.exe"
New-Item -ItemType Directory -Force -Path C:\e2-mayo\out | Out-Null
$log = "C:\e2-mayo\out\e2_batch.log"
"E2 batch start $(Get-Date -Format o)" | Tee-Object $log
Get-ChildItem C:\e2-mayo\step\*.stp | ForEach-Object {
    $b = $_.BaseName
    $glb = "C:\e2-mayo\out\$b.glb"
    $usd = "C:\e2-mayo\out\$b.usdc"
    "=== $b ===" | Tee-Object $log -Append
    & $mayo --no-progress -e $glb $_.FullName *>> $log
    $mExit = $LASTEXITCODE
    $gExit = "skip"
    if (Test-Path $glb) {
        & $guc $glb $usd *>> $log
        $gExit = $LASTEXITCODE
    }
    "$b mayo=$mExit guc=$gExit glb=$([bool](Test-Path $glb)) usd=$([bool](Test-Path $usd))" | Tee-Object $log -Append
}
"E2 batch end $(Get-Date -Format o)" | Tee-Object $log -Append
Get-ChildItem C:\e2-mayo\out | Select-Object Name, Length
