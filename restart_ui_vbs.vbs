Set objShell = CreateObject("WScript.Shell")
' Kill any existing process on port 5105
objShell.Run "cmd /c for /f ""tokens=5"" %p in ('netstat -ano ^| findstr "":5105 ""') do taskkill /PID %p /F", 0, True
WScript.Sleep 1000
' Start the new server
objShell.Run "cmd /c cd /d ""c:\Users\3KOM\monsfer_project_final\monsfer-server\MONITORING_UI"" && ""c:\Users\3KOM\monsfer_project_final\monsfer-server\venv\Scripts\python.exe"" app.py > app_ui.log 2>&1", 0, False
WScript.Sleep 3000
