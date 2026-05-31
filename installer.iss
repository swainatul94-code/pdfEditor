; Inno Setup script for pdf_app
; Build dist\pdf_app.exe via build.ps1 first.
; Compile: iscc installer.iss  (or open in Inno Setup Compiler GUI)

#define MyAppName        "pdf_app"
#define MyAppVersion     "0.1.0"
#define MyAppPublisher   "pdf_app"
#define MyAppExeName     "pdf_app.exe"
#define MyAppURL         "https://example.invalid/pdf_app"

[Setup]
AppId={{51947B8B-962E-454E-9083-00C90B38ADB3}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=pdf_app-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
#if FileExists(AddBackslash(SourcePath) + "icon.ico")
SetupIconFile=icon.ico
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\pdf_app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; Bundle requirements doc for reference
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; ---------- External dependency detection ----------
[Code]
const
  LIBREOFFICE_URL = 'https://www.libreoffice.org/download/download/';
  GTK_URL        = 'https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases';

function LibreOfficeInstalled(): Boolean;
var
  Paths: TArrayOfString;
  I: Integer;
  Names: TArrayOfString;
begin
  Result := False;
  // Common install locations
  Paths := ['{pf}\LibreOffice\program\soffice.exe',
            '{pf32}\LibreOffice\program\soffice.exe'];
  for I := 0 to GetArrayLength(Paths) - 1 do
    if FileExists(ExpandConstant(Paths[I])) then
    begin
      Result := True;
      Exit;
    end;
  // Registry key fallback
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\LibreOffice\LibreOffice', Names) and
     (GetArrayLength(Names) > 0) then
    Result := True;
end;

function GtkRuntimeInstalled(): Boolean;
var
  Names: TArrayOfString;
begin
  Result := False;
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\GTK\3.0', Names) and
     (GetArrayLength(Names) > 0) then
  begin
    Result := True;
    Exit;
  end;
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\WOW6432Node\GTK\3.0', Names) and
     (GetArrayLength(Names) > 0) then
    Result := True;
end;

procedure OpenURL(const URL: string);
var
  ErrorCode: Integer;
begin
  ShellExec('open', URL, '', '', SW_SHOW, ewNoWait, ErrorCode);
end;

function InitializeSetup(): Boolean;
var
  Msg: string;
  MissingLO, MissingGTK: Boolean;
begin
  Result := True;
  MissingLO := not LibreOfficeInstalled();
  MissingGTK := not GtkRuntimeInstalled();
  if MissingLO or MissingGTK then
  begin
    Msg := 'Optional dependencies missing:' + #13#10;
    if MissingLO then
      Msg := Msg + #13#10 + '  - LibreOffice (needed for docx/xlsx/pptx -> PDF)';
    if MissingGTK then
      Msg := Msg + #13#10 + '  - GTK runtime (needed for HTML/Markdown -> PDF via WeasyPrint)';
    Msg := Msg + #13#10 + #13#10 +
      'pdf_app will install without them. PDF viewing/editing/signing works' + #13#10 +
      'but the listed conversions will fail until the deps are installed.' + #13#10 + #13#10 +
      'Open download pages now?';
    if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES then
    begin
      if MissingLO then OpenURL(LIBREOFFICE_URL);
      if MissingGTK then OpenURL(GTK_URL);
    end;
  end;
end;
