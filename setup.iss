; setup.iss - Inno Setup script: classic wizard installer for Naji
; Output: Output\NajiSetup.exe  (the ONLY file you distribute)
;
; IMPORTANT: Inno Setup does NOT allow comments after a value on the
; same line. Keep every comment on its own line (starting with ";").
;
; Prerequisite: build dist\Naji.exe first (double-click build_exe.bat).
; Compile: double-click build_setup.bat, OR open this file in Inno Setup
; Compiler and press Build > Compile (Ctrl+F9).
; Wizard pages the end user sees:
;   1) Language (Farsi / English)
;   2) Welcome
;   3) Choose install drive/folder (like MSI Afterburner)
;   4) Start menu folder
;   5) Desktop icon (optional)
;   6) Review + Install + auto-launch at the end

#define MyAppName "Naji"
#define MyAppVersion "6.1.0"
#define MyAppPublisher "Naji"
#define MyAppExeName "Naji.exe"

[Setup]
AppId={{B7B3B8D2-6C7A-4E3F-9C4A-2F5C2B7B6A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Naji
DefaultGroupName={#MyAppName}
; classic full wizard: welcome + drive/folder + start-menu pages
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
; output file
OutputDir=Output
OutputBaseFilename=NajiSetup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; normal user can install (no admin needed); the default folder is
; per-user Programs and any drive (D:\ ...) can be picked next page
PrivilegesRequired=lowest
; installer file metadata
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoDescription=Setup - {#MyAppName} {#MyAppVersion}
;
; ---- v6.0: Authenticode signing of the installer (and uninstaller) ----
; Prerequisite (one-time, Inno Setup menu: Tools > Configure Sign Tools):
;   Name:   signtool
;   Path:   C:\Program Files (x86)\Windows Kits\10\bin\10.0.xxxxx.0\x64\signtool.exe
; Password comes from the environment variable NAJI_CERT_PASS so it is
; never stored in this file. If signtool is not configured, the two lines
; below are safely ignored by the compiler and the installer stays
; unsigned. Full guide: docs\CODE_SIGNING.md
SignTool=signtool $p $qNAJI_CERT_PASS$q /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com $f
SignedUninstaller=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; Farsi.isl ships WITH the project (same folder as this file)
Name: "farsi"; MessagesFile: "Farsi.isl"

[CustomMessages]
english.UninstallNaji=Uninstall %1
farsi.UninstallNaji=حذف %1

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallNaji,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; user settings in %APPDATA%\Naji are kept on purpose so a
; reinstall never wipes them
