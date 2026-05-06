; ================================================
;  Crazyflie Client - Inno Setup Installer Script
; ================================================

[Setup]
AppName=Crazyflie 客户端
AppId={{B1C8D3E0-FA2B-4C6E-9D1A-5E7F8A9B0C2D}}
AppVersion=1.0
AppPublisher=Bitcraze AB
AppPublisherURL=https://www.bitcraze.io
AppSupportURL=https://www.bitcraze.io
AppUpdatesURL=https://www.bitcraze.io
DefaultDirName={autopf}\CrazyflieClient
DefaultGroupName=Crazyflie 客户端
OutputDir=..\..\dist\installer
OutputBaseFilename=CrazyflieClient_Setup
SetupIconFile=..\..\src\cfclient\ui\icons\cfclient.ico
UninstallDisplayIcon={app}\cfclient.exe
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
Source: "..\..\dist\cfclient.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Crazyflie 客户端"; Filename: "{app}\cfclient.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 Crazyflie 客户端"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Crazyflie 客户端"; Filename: "{app}\cfclient.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\cfclient.exe"; Description: "启动 Crazyflie 客户端"; Flags: nowait postinstall shellexec skipifsilent
