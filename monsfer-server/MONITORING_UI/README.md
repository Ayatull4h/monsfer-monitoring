# Radio Spectrum Monitoring Dashboard

A Flask-based web application for monitoring and analyzing radio frequency spectrum data. The dashboard provides real-time visualization of spectrum data, device status monitoring, and alert management.

## Features

- Real-time spectrum visualization using Vue.js and ECharts
- Device status monitoring
- Alert system for spectrum anomalies
- Historical data analysis
- Responsive web interface

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Jalankan server menggunakan batch script:
```bash
run-server.bat
```

Atau jalankan via WSGI:
```bash
python wsgi.py
```

2. Buka browser dan akses:
```
http://127.0.0.1:5002
```

## API Endpoints

- `GET /api/spectrum` - Get current spectrum data
- `GET /api/devices` - Get device status information
- `GET /api/spectrum/history` - Get historical spectrum data
- `GET /api/alerts` - Get current alerts

## Project Structure

```
.
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   └── index.html     # Main dashboard template
└── spectrum.db        # SQLite database (created on first run)
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.