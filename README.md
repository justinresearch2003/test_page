# ⚠️ ReportGenerateApp  
### Interactive Attack Chain Reporting & Infrastructure Visualization Tool

ReportGenerateApp is a lightweight offensive security reporting engine built with Flask.  
It transforms compromise data into structured infrastructure reports and dynamic, interactive attack chain visualizations.

Designed for red team engagements, CTF documentation, and lab tracking.

---

## 🚀 Features

### 🟢 Compromised Host Tracking
- Track active shells
- Privilege level visibility (SYSTEM, Administrator, Web Shell)
- Subnet-based grouping
- Infrastructure segmentation

### 🔴 Credential Harvesting Table
- Source tracking (`.env`, config files, DB dumps, etc.)
- Target host mapping
- Credential validation status
- Pivot visibility

### 🗺️ Interactive Attack Map (SVG Engine)
- Dynamic subnet zones
- Credential-to-host relationships
- Pivot path visualization
- Zoom & pan support
- Host filtering (DC, DB, Linux, Windows, WebApp, Creds)
- Real-time search
- Severity-based node styling

### 📄 Report Generation
- Structured HTML report
- Optional inclusion of interactive attack map
- Print-ready PDF mode
- Clean dark-mode UI (Red Team HUD style)

---

## 🧠 Use Cases

- Red Team engagement documentation
- Internal lab attack tracking
- CTF writeups
- Infrastructure compromise mapping
- Attack chain visualization
- Credential pivot analysis

---

## 🛠 Tech Stack

- **Python 3**
- **Flask**
- Vanilla JavaScript (no frontend framework)
- SVG-based graph rendering
- Custom CSS HUD interface

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/ReportGenerateApp.git
cd ReportGenerateApp

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## ▶️ Running the Application

```bash
python web_app.py
```

Default:
```
http://127.0.0.1:5000
```

---

## 📂 Project Structure

```
ReportGenerateApp/
│
├── web_app.py               # Main Flask application
├── report_generator.py      # Report generation logic
├── attack_map.html          # SVG-based attack chain visualization
├── generated_report.html    # Generated report output
├── bundled_report.html      # Combined report + map
├── requirements.txt
└── .gitignore
```

---

## 🗺️ Attack Map Architecture

The visualization engine:

- Groups nodes by subnet zones
- Maps credential relationships
- Tracks pivot movement across hosts
- Uses severity-based color coding
- Supports interactive filtering
- Renders using pure SVG (no external graph libraries)

This allows complete portability and lightweight deployment.

---

## 🎯 Design Philosophy

- No heavy frontend frameworks
- No external graph dependencies
- Clean offensive-security aesthetic
- Fast generation & export
- Minimal attack surface

---

## 🔒 Security Note

This tool is intended for:
- Authorized security testing
- Educational purposes
- Lab environments

The developer is not responsible for misuse.

---

## 📌 Roadmap

- [ ] JSON-based dynamic data ingestion
- [ ] Multi-engagement support
- [ ] Graph analytics (shortest pivot path)
- [ ] Export to structured pentest report template
- [ ] Dockerized deployment
- [ ] Role-based multi-user mode

---

## 🧑‍💻 Author

Developed by Shohruh Yuldashev  
Offensive Security & Infrastructure Research

---

## 📜 License
ReportGenerateApp License

Copyright (c) 2026 Shohruh Yuldashev

Permission is granted to use, copy, and modify this software for:

- Personal use
- Educational purposes
- Research and non-commercial security testing

Commercial use is strictly prohibited.

You may NOT:
- Sell this software
- Redistribute it for profit
- Use it in commercial products or services
- Rebrand and sell it as your own product

This software is provided "as is", without warranty of any kind.
The author is not responsible for any misuse.

For commercial licensing inquiries, contact the author.

