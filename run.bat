@echo off
chcp 65001 > nul
title AI Career & Interview Coach - Launcher

echo =======================================================
echo    🚀 AI Career & Interview Coach - Starting Up
echo =======================================================
echo.

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org/ (LTS version recommended).
    echo.
    pause
    exit /b 1
)

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python 3 is not installed or not in PATH!
        echo Please install Python 3.10+ from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

:: Run unified cross-platform launcher
node scripts\run.js

if %errorlevel% neq 0 (
    echo.
    echo Launcher encountered an error. Press any key to exit.
    pause
)
