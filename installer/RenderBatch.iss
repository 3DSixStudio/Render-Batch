; Inno Setup script for Render Batch
; Build:  ISCC /DMyAppVersion=1.4.0 installer\RenderBatch.iss   (after PyInstaller -> dist\RenderBatch)

#define MyAppName "Render Batch"
#define MyAppExe "RenderBatch.exe"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{9C1E7B52-3D7A-4F6B-9A0E-5B2C8E4D1A77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Hari
AppPublisherURL=https://github.com/3DSixStudio/Render-Batch
AppSupportURL=https://github.com/3DSixStudio/Render-Batch/releases
DefaultDirName={localappdata}\Programs\Render Batch
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist_installer
OutputBaseFilename=Render_Batch_Setup_v{#MyAppVersion}
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; remove files of the previous version before copying the new ones
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\RenderBatch\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
; also runs after a silent update, so the app reopens by itself
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall
