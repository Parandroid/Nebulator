@echo off
echo Removing virtual environment...
if exist venv (
    rmdir /s /q venv
    echo Clean complete!
) else (
    echo Virtual environment not found.
)


