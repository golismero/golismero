@echo off
del cython.log > nul 2> nul
cd ..\golismero
dir /b /s *.py > ..\_tmp.txt
cd ..\plugins
dir /b /s *.py >> ..\_tmp.txt
cd ..\tests\plugin_tests
dir /b /s *.py >> ..\_tmp.txt
cd ..\..
del /s *.c > nul 2> nul
del /s *.pyc > nul 2> nul
del /s *.pyo > nul 2> nul
for /F "tokens=*" %%A in (_tmp.txt) do (
    C:\Python27\python.exe C:\Python27\Scripts\cython.py "%%A" 2>> tests\cython.log
)
del _tmp.txt > nul 2> nul
del /s *.c > nul 2> nul
cd tests
del _tmp.txt > nul 2> nul
