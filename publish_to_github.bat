@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_to_github.ps1" %*
