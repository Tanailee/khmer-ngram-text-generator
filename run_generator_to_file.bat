@echo off
chcp 65001 > nul
set PYTHONUTF8=1
python -X utf8 mini_project_1_ngram.py --seed-file input_seed.txt --model backoff --length 45 --output generated_text.txt
echo.
echo Open generated_text.txt to see the Khmer generated result.
pause
