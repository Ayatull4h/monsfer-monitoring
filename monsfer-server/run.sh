#!/bin/bash
source /home/monsfer-server/monsfer-server/venv/bin/activate
cd /home/monsfer-server/monsfer-server/MONITORING_UI/ && gunicorn --workers 3 --bind unix:/tmp/monitoring.sock wsgi:app &
cd /home/monsfer-server/monsfer-server && python server.py &
#cd /home/monsfer-server/monsfer-server/script && python app.py &
