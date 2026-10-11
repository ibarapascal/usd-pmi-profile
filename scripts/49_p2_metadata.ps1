# R1 T8c（回应 R2-9）：P2 Omniverse hoops_core 511.3.2 以 convertMetadata=true 重转 7 月同一批 17 件 AP242 输入，
# 并在同一会话以默认配置再转一遍作 A/B 对照（隔离「选项」与「重装/时间」两种差异）。
# 必须在 Windows 工作站上以**安装 usd-convert-cad 的桌面用户本人**运行：venv 的基础 Python 与 Kit 扩展缓存
# （%LOCALAPPDATA%\ov\data）都在该用户 profile 内，作业调度器的服务账户读不到（2026-10-05 探测实证）。
# 用法（工作站桌面 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File <工作目录>\49_p2_metadata.ps1
# 输出：C:\omniverse\usd-cad\batch-metadata\<name>.meta.{usdc,report.json,hoops.log,run.log}
#       C:\omniverse\usd-cad\batch-default-r1\<name>.default.{usdc,report.json,hoops.log,run.log}
#       C:\omniverse\usd-cad\batch-metadata\t8_master.log（逐件起止与退出码）
# 只读输入 C:\omniverse\usd-cad\batch\*.stp（7 月 batch_convert.bat 的同一批），只写上面两个新目录；全在 C 盘。
# 之后在 Mac 侧：把两个目录拷回 out/r1/t8/pcb/，跑 49_p2_metadata.py 扫描与逐件 diff。
# （2026-10-05 去标识：注释中的机器名／用户 profile 路径／调度器工作目录改为通称，代码行未动）
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:OMNI_KIT_ACCEPT_EULA = "yes"      # 与 7 月 batch_convert.bat 相同（EULA 已由用户在安装时接受，见 install.log）
$Repo = "C:\omniverse\usd-convert-cad"
$In = "C:\omniverse\usd-cad\batch"
$OutM = "C:\omniverse\usd-cad\batch-metadata"
$OutD = "C:\omniverse\usd-cad\batch-default-r1"
New-Item -ItemType Directory -Force -Path $OutM, $OutD | Out-Null
$Log = Join-Path $OutM "t8_master.log"
"T8 start $(Get-Date -Format o) user=$env:USERNAME" | Out-File -Encoding utf8 $Log
Set-Location $Repo
$files = Get-ChildItem -Path $In -Filter *.stp | Sort-Object Name
"inputs=$($files.Count)" | Out-File -Append -Encoding utf8 $Log
foreach ($f in $files) {
  $n = $f.BaseName
  foreach ($cfg in @(@{tag="meta"; dir=$OutM; opt=@("--option","convertMetadata=true")},
                     @{tag="default"; dir=$OutD; opt=@()})) {
    $base = Join-Path $cfg.dir "$n.$($cfg.tag)"
    $t0 = Get-Date
    & py -3.12 convert.py $f.FullName "$base.usdc" --report "$base.report.json" --log "$base.hoops.log" @($cfg.opt) *> "$base.run.log"
    $code = $LASTEXITCODE
    "$n $($cfg.tag) exit=$code sec=$([math]::Round(((Get-Date)-$t0).TotalSeconds,1))" | Out-File -Append -Encoding utf8 $Log
  }
}
"T8 done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 $Log
Write-Host "T8 done. See $Log"
