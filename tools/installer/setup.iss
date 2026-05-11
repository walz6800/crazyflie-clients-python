; ================================================
;  Aeroflie Client - Inno Setup Installer Script
; ================================================

[Setup]
AppName=FormflieHub
AppId={{B1C8D3E0-FA2B-4C6E-9D1A-5E7F8A9B0C2D}}
AppVersion=1.0
AppPublisher=广州维脉电子科技有限公司
AppPublisherURL=#
AppSupportURL=#
AppUpdatesURL=#
DefaultDirName={autopf}\FormflieHub
DefaultGroupName=FormflieHub
OutputDir=..\..\dist\installer
OutputBaseFilename=FormflieHub_Setup
SetupIconFile=..\..\src\cfclient\ui\icons\cfclient.ico
UninstallDisplayIcon={app}\FormflieHub.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他快捷方式："; Flags: checkedonce

[Files]
Source: "..\..\dist\FormflieHub.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FormflieHub"; Filename: "{app}\FormflieHub.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 FormflieHub"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FormflieHub"; Filename: "{app}\FormflieHub.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\FormflieHub.exe"; Description: "启动 FormflieHub"; Flags: nowait postinstall shellexec skipifsilent
