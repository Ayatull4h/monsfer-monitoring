Set objShell = CreateObject("WScript.Shell")
objShell.Run "cmd /c cd /d ""c:\Users\3KOM\monsfer_project_final\monsfer-server\MONITORING_UI"" && ""c:\Users\3KOM\monsfer_project_final\monsfer-server\venv\Scripts\python.exe"" app.py > app_ui.log 2>&1", 0, False
WScript.Sleep 4000
