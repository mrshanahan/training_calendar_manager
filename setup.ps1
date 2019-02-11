param (
    [Parameter(Position=0)]
    [string] $RootDirectory = $PSScriptRoot
)

function exec([ScriptBlock] $Block)
{
    $oldLastExitCode = $LASTEXITCODE
    $LASTEXITCODE = 0
    & $Block
    if ($LASTEXITCODE -ne 0)
    {
        throw "Block error out with exit code $LASTEXITCODE"
    }
    $LASTEXITCODE = $oldLastExitCode
}

$root = (Resolve-Path $RootDirectory).Path

Push-Location $RootDirectory
try
{
    if (-not (Test-Path Env:\VIRTUAL_ENV))
    {
        Write-Host "Creating virtualenv in ${RootDirectory}..."
        exec { & virtualenv . }
    
        Write-Host "Activating virtualenv..."
        $venvScripts = Join-Path $root 'Scripts'
        exec { & (Join-Path $venvScripts 'activate.ps1') }
    }

    Write-Host "Installing dependencies..."
    exec { & pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib }

    $credentialsPath = Join-Path $PSScriptRoot 'credentials.json'
    while (-not (Test-Path $credentialsPath))
    {
        Write-Host "Credentials not found. Visit this URL and click on the button in step 1 and download credentials to ${credentialsPath}:`nhttps://developers.google.com/google-apps/calendar/quickstart/python"
        Read-Host -Prompt "Press enter when downloaded"
    }

    Write-Host "Setup complete!"
}
finally
{
    Pop-Location
}


