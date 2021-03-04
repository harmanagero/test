$testchoco = powershell choco -v
if(-not($testchoco)){
    Write-Output "Seems Chocolatey is not installed, installing now"

    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    }
else{
    Write-Output "Chocolatey Version $testchoco is already installed"
}

$url = "https://www.python.org/ftp/python/3.8.6/python-3.8.6-amd64.exe"
$output = "C:/tmp/python-3.8.6-amd64.exe"

if (Test-Path $output) {
    Write-Host "Script exists - skipping installation"
    return;
}
else
{
    New-Item -ItemType Directory -Force -Path C:/tmp

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $output


    & $output /passive InstallAllUsers=1 PrependPath=1 Include_test=0
}


$testpip = powershell pip --version
if(-not($testpip)){

    Write-Output "Pip is not installed, installing now"

    # Install pip
    choco install pip

    }
else{
    Write-Output "Pip Version $testpip is already installed"
}

$testpipenv = powershell pipenv --version
if(-not($testpipenv)){

    Write-Output "Pipenv is not installed, installing now"

    # Install pipenv
    pip install pipenv

    }
else{
    pipenv --version
    Write-Output "Pipenv Version $testpip is already installed"
}


Write-Output "Docker Desktop is not installed, installing now"

# Install Docker Desktop
Choco install docker-desktop

Write-Output "Docker Desktop Finished installing."



$testmake = powershell make --version
if(-not($testmake)){

    Write-Output "Make is not installed, installing now"

    # Install make
    choco install mingw

    }
else{
    Write-Output "Make Version $testmake is already installed"
}
