; Inno Setup script. Compile with setup_and_build.bat (needs Inno Setup 6).
#define AppName "Smartschool Planner"
#define AppExe "SmartschoolPlanner.exe"
#ifndef AppVersion
  #define AppVersion "2.1.2"  ; the release workflow passes the real one from version.py
#endif

[Setup]
AppId={{B7C1E2A4-5D3F-4E8A-9A61-2F0C8D7E1B55}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\SmartschoolPlanner
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=SmartschoolPlanner-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
LicenseFile=LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
CloseApplicationsFilter={#AppExe}
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "dist\SmartschoolPlanner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autoprograms}\{#AppName} - Change login details"; Filename: "{app}\{#AppExe}"; Parameters: "--setup"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "{code:LaunchParameters}"; Description: "Launch {#AppName}"; Flags: nowait postinstall

[Code]
var
  WasUpgrade: Boolean;

function LaunchParameters(Param: String): String;
begin
  if WasUpgrade then Result := '--updated' else Result := '';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    WasUpgrade := FileExists(ExpandConstant('{app}\{#AppExe}'));
  if CurStep = ssPostInstall then
  begin
    if WasUpgrade then
    begin
      if FileExists(ExpandConstant('{app}\data\rendering_choice_pending')) and
         (not DeleteFile(ExpandConstant('{app}\data\rendering_choice_pending'))) then
        RaiseException('Could not clear the first-start rendering choice.');
    end
    else
    begin
      ForceDirectories(ExpandConstant('{app}\data'));
      if not SaveStringToFile(ExpandConstant('{app}\data\rendering_choice_pending'), 'pending', False) then
        RaiseException('Could not save the first-start rendering choice.');
    end;
  end;

end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var RC: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    if FileExists(ExpandConstant('{app}\{#AppExe}')) then
      if not Exec(ExpandConstant('{app}\{#AppExe}'), '--clear-credentials', '',
        SW_HIDE, ewWaitUntilTerminated, RC) then
        RaiseException('Could not remove saved login details. Close the app and retry uninstalling.')
      else if RC <> 0 then
        RaiseException('Windows could not remove saved login details. Retry uninstalling under the account that installed the app.');
  end;
end;

[UninstallDelete]
; remove the nonsecret vault reference and local planner data
Type: files; Name: "{app}\credentials.yml"
Type: files; Name: "{app}\credentials.recovery.bin"
Type: filesandordirs; Name: "{app}\data"
Type: files; Name: "{app}\dashboard.html"
