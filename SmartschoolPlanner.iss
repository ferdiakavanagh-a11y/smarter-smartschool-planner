; Inno Setup script. Compile with build_installer.bat (needs Inno Setup 6).
#define AppName "Smartschool Planner"
#define AppExe "SmartschoolPlanner.exe"
#define AppVersion "2.0.0"

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

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autoprograms}\{#AppName} - Change login details"; Filename: "{app}\{#AppExe}"; Parameters: "--setup"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  CredPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  CredPage := CreateInputQueryPage(wpSelectDir, 'Smartschool login',
    'Enter your Smartschool details', 'They are saved only on this computer.');
  CredPage.Add('Username:', False);
  CredPage.Add('Password:', True);
  CredPage.Add('School address (e.g. yourschool.smartschool.be):', False);
  CredPage.Add('Security answer: birthdate as YYYY-MM-DD, or 2FA secret (optional):', False);
  CredPage.Add('Gemini API key (optional, enables deadline detection):', False);
end;

function CredFile: String;
begin
  Result := WizardDirValue + '\credentials.yml';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  { keep existing login details when reinstalling/updating }
  Result := (PageID = CredPage.ID) and FileExists(CredFile);
end;

function CleanUrl(S: String): String;
var P: Integer;
begin
  S := Trim(S);
  StringChangeEx(S, 'https://', '', True);
  StringChangeEx(S, 'http://', '', True);
  P := Pos('/', S);
  if P > 0 then S := Copy(S, 1, P - 1);
  Result := Trim(S);
end;

function Q(S: String): String;
begin
  StringChangeEx(S, '\', '\\', True);
  StringChangeEx(S, '"', '\"', True);
  Result := '"' + S + '"';
end;

function NormalizeSecurity(S: String; var Bad: Boolean): String;
var
  I, P: Integer;
  A, B, C, Rest, Y, M, D: String;
  DateLike: Boolean;
begin
  Bad := False;
  S := Trim(S);
  Result := S;
  if S = '' then Exit;
  DateLike := True;
  for I := 1 to Length(S) do
    if Pos(S[I], '0123456789-./') = 0 then DateLike := False;
  if not DateLike then Exit;  { e.g. a 2FA secret: keep as is }

  if (Length(S) = 8) and (Pos('-', S) = 0) and (Pos('.', S) = 0) and (Pos('/', S) = 0) then
  begin
    Y := Copy(S, 1, 4); M := Copy(S, 5, 2); D := Copy(S, 7, 2);
  end else
  begin
    StringChangeEx(S, '.', '-', True);
    StringChangeEx(S, '/', '-', True);
    P := Pos('-', S);
    if P = 0 then begin Bad := True; Exit; end;
    A := Copy(S, 1, P - 1);
    Rest := Copy(S, P + 1, Length(S));
    P := Pos('-', Rest);
    if P = 0 then begin Bad := True; Exit; end;
    B := Copy(Rest, 1, P - 1);
    C := Copy(Rest, P + 1, Length(Rest));
    if (Pos('-', C) > 0) or (A = '') or (B = '') or (C = '') then begin Bad := True; Exit; end;
    if (Length(A) = 4) and (Length(C) <= 2) then
    begin
      Y := A; M := B; D := C;
    end else if (Length(C) = 4) and (Length(A) <= 2) then
    begin
      Y := C; M := B; D := A;
    end else
    begin
      Bad := True; Exit;
    end;
  end;
  if Length(M) = 1 then M := '0' + M;
  if Length(D) = 1 then D := '0' + D;
  if (StrToIntDef(M, 0) < 1) or (StrToIntDef(M, 0) > 12) or
     (StrToIntDef(D, 0) < 1) or (StrToIntDef(D, 0) > 31) then
  begin
    Bad := True; Exit;
  end;
  Result := Y + '-' + M + '-' + D;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Bad: Boolean;
begin
  Result := True;
  if CurPageID = CredPage.ID then
  begin
    NormalizeSecurity(CredPage.Values[3], Bad);
    if Bad then
    begin
      MsgBox('Birthdate must be in YYYY-MM-DD format, e.g. 2008-05-14.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if (Trim(CredPage.Values[0]) = '') or (CredPage.Values[1] = '') or (CleanUrl(CredPage.Values[2]) = '') then
    begin
      MsgBox('Username, password and school address are required.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  L: TArrayOfString;
  Mfa: String;
  RC: Integer;
  Bad: Boolean;
begin
  if (CurStep = ssPostInstall) and (not FileExists(CredFile)) then
  begin
    Mfa := NormalizeSecurity(CredPage.Values[3], Bad);
    if Mfa = '' then Mfa := 'REPLACE_ME';
    SetArrayLength(L, 6);
    L[0] := 'username: ' + Q(Trim(CredPage.Values[0]));
    L[1] := 'password: ' + Q(CredPage.Values[1]);
    L[2] := 'main_url: ' + Q(CleanUrl(CredPage.Values[2]));
    L[3] := 'mfa: ' + Q(Mfa);
    L[4] := 'gemini_api_key: ' + Q(Trim(CredPage.Values[4]));
    L[5] := 'planner_detail_url: ""';
    SaveStringsToUTF8File(CredFile, L, False);
    { owner-only access }
    Exec('icacls', '"' + CredFile + '" /inheritance:r /grant:r "' + GetUserNameString + ':F"',
      '', SW_HIDE, ewWaitUntilTerminated, RC);
  end;
end;

[UninstallDelete]
; credentials contain a password: remove them with the app
Type: files; Name: "{app}\credentials.yml"
Type: filesandordirs; Name: "{app}\data"
Type: files; Name: "{app}\dashboard.html"
