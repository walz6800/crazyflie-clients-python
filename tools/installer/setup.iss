; ================================================
;  Crazyflie Client - Inno Setup Installer Script
; ================================================

[Setup]
AppName=wcfCtrlSystem
AppId={{B1C8D3E0-FA2B-4C6E-9D1A-5E7F8A9B0C2D}}
AppVersion=1.0
AppPublisher=广州维脉电子科技有限公司
AppPublisherURL=https://www.bitcraze.io
AppSupportURL=https://www.bitcraze.io
AppUpdatesURL=https://www.bitcraze.io
DefaultDirName={autopf}\wcfCtrlSystem
DefaultGroupName=wcfCtrlSystem
OutputDir=..\..\dist\installer
OutputBaseFilename=wcfCtrlSystem_Setup
SetupIconFile=..\..\src\cfclient\ui\icons\cfclient.ico
UninstallDisplayIcon={app}\wcfCtrlSystem.exe
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
Source: "..\..\dist\wcfCtrlSystem.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\wcfCtrlSystem"; Filename: "{app}\wcfCtrlSystem.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 wcfCtrlSystem"; Filename: "{uninstallexe}"
Name: "{autodesktop}\wcfCtrlSystem"; Filename: "{app}\wcfCtrlSystem.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\wcfCtrlSystem.exe"; Description: "启动 wcfCtrlSystem"; Flags: nowait postinstall shellexec skipifsilent
