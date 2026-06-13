@echo off
chcp 65001 > nul
set PYTHONUTF8=1
python -X utf8 mini_project_1_ngram.py --interactive
pause
