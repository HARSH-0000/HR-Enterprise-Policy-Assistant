# ============================================================
# Dependency Check and Update Script
# ============================================================

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    HR Enterprise Assistant - Dependency Check             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "🐍 Checking Python Version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   $pythonVersion" -ForegroundColor White

if ($pythonVersion -notmatch "3\.1[0-2]") {
    Write-Host "   ⚠️  Warning: Python 3.10-3.12 recommended" -ForegroundColor Red
} else {
    Write-Host "   ✅ Python version OK" -ForegroundColor Green
}

Write-Host ""

# Check Node version
Write-Host "📦 Checking Node.js Version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
Write-Host "   $nodeVersion" -ForegroundColor White

if ($nodeVersion -notmatch "v(1[8-9]|2[0-9])\.") {
    Write-Host "   ⚠️  Warning: Node.js 18+ recommended" -ForegroundColor Red
} else {
    Write-Host "   ✅ Node.js version OK" -ForegroundColor Green
}

Write-Host ""

# Check Docker
Write-Host "🐳 Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "   $dockerVersion" -ForegroundColor White
    Write-Host "   ✅ Docker installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker not installed" -ForegroundColor Red
}

Write-Host ""

# Backend Dependencies
Write-Host "📚 Backend Dependencies Status..." -ForegroundColor Yellow
cd backend

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ Virtual environment exists" -ForegroundColor Green
    
    .\venv\Scripts\Activate.ps1
    
    Write-Host "   📦 Checking installed packages..." -ForegroundColor Gray
    $packages = pip list --format=json | ConvertFrom-Json
    
    $required = @{
        "fastapi" = "0.115.5"
        "uvicorn" = "0.32.1"
        "langchain" = "0.3.14"
        "pinecone" = "5.4.2"
        "sentence-transformers" = "3.3.1"
    }
    
    foreach ($pkg in $required.Keys) {
        $installed = $packages | Where-Object { $_.name -eq $pkg }
        if ($installed) {
            if ($installed.version -eq $required[$pkg]) {
                Write-Host "      ✅ $pkg ($($installed.version))" -ForegroundColor Green
            } else {
                Write-Host "      ⚠️  $pkg ($($installed.version)) - Expected: $($required[$pkg])" -ForegroundColor Yellow
            }
        } else {
            Write-Host "      ❌ $pkg - Not installed" -ForegroundColor Red
        }
    }
    
    deactivate 2>$null
} else {
    Write-Host "   ❌ Virtual environment not found" -ForegroundColor Red
    Write-Host "   Run: python -m venv venv" -ForegroundColor Gray
}

cd ..
Write-Host ""

# Frontend Dependencies
Write-Host "🎨 Frontend Dependencies Status..." -ForegroundColor Yellow
cd frontend

if (Test-Path "node_modules") {
    Write-Host "   ✅ node_modules exists" -ForegroundColor Green
    
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    $installedVersion = $packageJson.version
    
    Write-Host "   📦 Application version: $installedVersion" -ForegroundColor White
    Write-Host "   ✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ❌ node_modules not found" -ForegroundColor Red
    Write-Host "   Run: npm install" -ForegroundColor Gray
}

cd ..
Write-Host ""

# Summary
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📋 Recommended Actions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend:" -ForegroundColor White
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  pip install --upgrade -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "Frontend:" -ForegroundColor White
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm install" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan