; Script de instalacion para Inno Setup
; Planificador Delivery Pro 2.1.3
;
; Compilar desde Inno Setup con:
;   ISCC.exe installer\PlanificadorDeliveryPro.iss

#define MyAppName "Planificador Delivery Pro"
#define MyAppPublisher "Planificador Delivery Pro"
#define MyAppVersion "2.1.3"
#define MyAppExeName "PlanificadorDeliveryPro.exe"
#define MyAppId "{{7A927C7D-51FD-4B78-A3C0-1F35A02F3B7D}"
#define SourceDir "..\dist\PlanificadorDeliveryPro"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=PlanificadorDeliveryPro-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=no
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\resources\icons\app.ico
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; Limpia recursos antiguos de la aplicacion instalada, sin tocar datos de usuario.
Type: filesandordirs; Name: "{app}\_internal"
