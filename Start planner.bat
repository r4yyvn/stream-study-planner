@echo off
cd /d "%~dp0"
title Stream ^& Study Planner
python server.py
if errorlevel 1 pause
