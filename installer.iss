[Setup]
AppName=AutoScan BR
AppVersion=2.0.0
DefaultDirName={autopf}\AutoScan BR
DefaultGroupName=AutoScan BR
OutputDir=C:\Users\admin\Desktop\elm327\releases
OutputBaseFilename=AutoScan_BR_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\admin\Desktop\elm327\dist\AutoScanBR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AutoScan BR"; Filename: "{app}\AutoScanBR.exe"
Name: "{autodesktop}\AutoScan BR"; Filename: "{app}\AutoScanBR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AutoScanBR.exe"; Description: "{cm:LaunchProgram,AutoScan BR}"; Flags: nowait postinstall skipifsilent

