#!/usr/bin/env python3
"""
Report Generator Bot for Infrastructure Assessments

This script generates HTML reports similar to the provided MOBI.UZ / UMS.UZ infrastructure map.
It uses a template-based approach to create dynamic reports.

Usage:
    python report_generator.py [options]

Options:
    --output FILE    Output HTML file (default: report.html)
    --data FILE      JSON file with report data (optional, uses defaults if not provided)
    --help           Show this help message
"""

import json
import argparse
from datetime import datetime

# Default data structure for the report
DEFAULT_DATA = {
    "title": "Infrastructure",
    "update_date": "2026-02-18 19:01 UTC",
    "stats": {}, # No stats bar in the provided HTML example
    "compromised_hosts": [
        {
            "ip": "192.168.10.10",
            "service": "WebApp",
            "tag": "Web Shell"
        },
        {
            "ip": "192.168.1.50",
            "service": "DC client",
            "tag": "NT /Authority SYSTEM"
        },
        {
            "ip": "192.168.1.5",
            "service": "DC admin",
            "tag": "Administrator"
        },
        {
            "ip": "192.168.20.15",
            "service": "DataBase",
            "tag": "Administrator"
        }
    ],
    "credentials": [
        {
            "source": "database.php",
            "credential": "<code>just:just</code>",
            "target": "192.168.10.10",
            "status": "✓ Valid"
        },
        {
            "source": "/.env",
            "credential": "<code>justin:P@ss!123</code>",
            "target": "192.168.1.50",
            "status": "✓ Valid"
        },
        {
            "source": "/admin/conf/files/.secret",
            "credential": "<code>db_admin:My_@dm!n</code>",
            "target": "192.168.20.15",
            "status": "✓ Valid"
        }
    ]
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0D1117; color: #C9D1D9; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.5; padding: 20px; }}
  .header {{ background: #161B22; border: 1px solid #BC8CFF; border-radius: 8px; padding: 20px 24px; margin-bottom: 16px; }}
  .header h1 {{ font-family: "Space Grotesk", sans-serif; font-size: 22px; color: #BC8CFF; font-weight: 700; letter-spacing: -0.5px; }}
  .header .meta {{ color: #8B949E; font-size: 11px; margin-top: 4px; }}
  .stats-bar {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
  .stat {{ background: #161B22; border: 1px solid #21262D; border-radius: 6px; padding: 10px 16px; text-align: center; flex: 1; min-width: 90px; }}
  .stat-value {{ font-size: 20px; font-weight: 700; color: #58A6FF; }}
  .stat-label {{ font-size: 10px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }}
  .container {{ display: flex; flex-direction: column; gap: 16px; }}
  .zone {{ border: 1px solid #21262D; border-radius: 8px; overflow: hidden; background: #0D1117; }}
  .zone-header {{ padding: 10px 16px; font-weight: 600; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }}
  .zone-count {{ font-size: 11px; font-weight: 400; padding: 2px 8px; border-radius: 10px; background: rgba(255,255,255,0.06); }}
  .zone.owned .zone-header {{ background: rgba(188,140,255,0.12); color: #BC8CFF; border-bottom: 1px solid rgba(188,140,255,0.2); }}
  .zone.critical .zone-header {{ background: rgba(248,81,73,0.12); color: #F85149; border-bottom: 1px solid rgba(248,81,73,0.2); }}
  .zone-body {{ padding: 12px; display: flex; flex-direction: column; gap: 6px; }}
  .host {{ display: flex; align-items: flex-start; gap: 12px; padding: 6px 10px; border-radius: 4px; background: #161B22; border: 1px solid #21262D; }}
  .host:hover {{ border-color: #30363D; }}
  .host-ip {{ min-width: 160px; color: #58A6FF; font-weight: 500; white-space: nowrap; font-size: 11px; }}
  .host-service {{ flex: 1; color: #C9D1D9; font-size: 11px; }}
  .host-service code {{ background: rgba(248,81,73,0.15); color: #F85149; padding: 1px 5px; border-radius: 3px; font-size: 10px; }}
  .host-tag {{ font-size: 9px; font-weight: 600; padding: 2px 6px; border-radius: 3px; white-space: nowrap; text-transform: uppercase; letter-spacing: 0.5px; }}
  .tag-owned {{ background: rgba(188,140,255,0.2); color: #BC8CFF; }}
  .creds-table, .users-table, .data-table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 16px; }}
  .creds-table th, .users-table th, .data-table th {{ text-align: left; padding: 8px 10px; background: #21262D; color: #58A6FF; font-weight: 600; border-bottom: 1px solid #30363D; }}
  .creds-table td, .users-table td, .data-table td {{ padding: 6px 10px; border-bottom: 1px solid #21262D; }}
  .creds-table tr:hover, .users-table tr:hover, .data-table tr:hover {{ background: rgba(88,166,255,0.04); }}
  .status-done {{ color: #3FB950; }} .status-fail {{ color: #F85149; }} .status-pending {{ color: #D29922; }} .status-locked {{ color: #F85149; font-style: italic; }}
  .footer-note {{ text-align: center; padding: 16px; font-size: 10px; color: #484F58; border-top: 1px solid #21262D; margin-top: 16px; }}
  .markdown-content {{ background: #161B22; border: 1px solid #21262D; border-radius: 8px; padding: 16px; }}
  .controls {{ position: absolute; top: 20px; right: 20px; display: flex; gap: 8px; }}
  .btn {{ background: #21262D; color: #c9d1d9; border: 1px solid #30363D; padding: 6px 12px; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 12px; transition: 0.2s; }}
  .btn:hover {{ background: #30363D; color: #58a6ff; border-color: #58a6ff; }}
  @media print {{
      @page {{ margin: 0; }}
      body {{ background: white; color: black; margin: 1.6cm; }}
      .header, .stat, .zone, .host, .markdown-content {{ background: white; border: 1px solid #ddd; color: black; }}
      .controls, .scanlines {{ display: none !important; }}
      .stat-value, .host-ip, .creds-table th, .header h1 {{ color: #000; }}
      .tag-owned {{ background: #eee; color: #000; border: 1px solid #ccc; }}
      a {{ text-decoration: none; color: black; }}
      .zone.owned .zone-header, .zone.critical .zone-header {{ background: #f0f0f0; color: #000; }}
  }}
  /* Modal Styles */
  .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 2000; display: none; align-items: center; justify-content: center; }}
  .modal {{ background: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 24px; max-width: 400px; width: 90%; box-shadow: 0 8px 24px rgba(0,0,0,0.5); text-align: center; }}
  .modal h3 {{ color: #C9D1D9; margin-bottom: 12px; font-family: "Space Grotesk", sans-serif; }}
  .modal p {{ color: #8B949E; font-size: 13px; margin-bottom: 24px; }}
  .modal-actions {{ display: flex; gap: 12px; justify-content: center; }}
  .btn-primary {{ background: #238636; color: white; border: none; }}
  .btn-primary:hover {{ background: #2ea043; }}
  .btn-secondary {{ background: #21262D; color: #C9D1D9; border: 1px solid #30363D; }}
  .btn-secondary:hover {{ background: #30363D; }}
</style>
</head>
<body>

<div class="header">
  <h1>⚠️ {title}</h1>
  <div class="meta">Compromised Hosts: {compromised_hosts_summary} | Updated: {update_date}</div>
</div>

<div class="stats-bar"></div>

<div class="container">

<!-- ═══════════════ COMPROMISED HOSTS ═══════════════ -->
<div class="zone owned">
  <div class="zone-header">🟢 COMPROMISED HOSTS — ACTIVE SHELLS<span class="zone-count">{num_hosts} HOSTS</span></div>
  <div class="zone-body">
    {compromised_hosts_html}
  </div>
</div>

<!-- ═══════════════ CREDENTIALS TABLE ═══════════════ -->
<div class="zone critical">
  <div class="zone-header">ALL HARVESTED CREDENTIALS<span class="zone-count">{num_creds}+</span></div>
  <div class="zone-body">
    <table class="creds-table">
      <tr><th>Source</th><th>Credential</th><th>Target</th><th>Status</th></tr>
      {credentials_html}
    </table>
  </div>
</div>

<!-- ═══════════════ USERS TABLE ═══════════════ -->


<!-- ═══════════════ ADDITIONAL DATA ═══════════════ -->


<!-- ═══════════════ MARKDOWN CONTENT ═══════════════ -->
Web service => Internal Network

</div>
</div>
<div class="footer-note">
  Infrastructure Assessment v6 — Generated {current_date} — {num_hosts} hosts compromised, compromised infrastructure mapped
</div>

<!-- Modal for Download Confirmation -->
<div class="modal-overlay" id="downloadModal">
  <div class="modal">
    <h3 id="modalTitle">Download Report</h3>
    <p id="modalDesc">Do you want to include the interactive Attack Map in the downloaded report?</p>
    <div class="modal-actions">
      <button class="btn btn-primary" onclick="confirmDownload(true)">Yes, Include Map</button>
      <button class="btn btn-secondary" onclick="confirmDownload(false)">No, Report Only</button>
    </div>
    <div style="margin-top: 16px;">
        <button class="btn" style="background:transparent; border:none; color: #58a6ff; font-size: 11px;" onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>

<script>
let promptType = 'html';

function showDownloadModal(type) {{
    promptType = type || 'html';
    const title = document.getElementById('modalTitle');
    const desc = document.getElementById('modalDesc');
    const container = document.getElementById('downloadModal');
    
    if (promptType === 'pdf') {{
        title.innerText = "Save as PDF";
        desc.innerText = "Do you want to include the Attack Map pages in the PDF?";
    }} else {{
        title.innerText = "Download Report";
        desc.innerText = "Do you want to include the interactive Attack Map in the file?";
    }}
    container.style.display = 'flex';
}}

function closeModal() {{
    document.getElementById('downloadModal').style.display = 'none';
}}

function confirmDownload(includeMap) {{
    const mapParam = includeMap ? '1' : '0';
    
    // Check if running standalone (file://)
    if (window.location.protocol === 'file:') {{
        if (promptType === 'pdf') {{
            if (includeMap) {{
                alert("Cannot include interactive map in PDF when running standalone. Please use the Web App for this feature.");
            }} else {{
                window.print();
            }}
        }} else {{
            // Download HTML - for standalone, this is tricky. 
            // Just alert user or maybe try to save page? 
            // Actually, if they have the file open, they already have it.
            alert("You are viewing a standalone report file. It is already downloaded.");
        }}
        closeModal();
        return;
    }}

    if (promptType === 'pdf') {{
        // Open view_report in new tab for printing
        if (includeMap) {{
            window.open('/view_report?include_map=' + mapParam, '_blank');
        }} else {{
            // If no map, just print current page to avoid opening new tab if possible, 
            // OR use view_report?include_map=0 (which we fixed to auto-print)
             window.open('/view_report?include_map=0', '_blank');
        }}
    }} else {{
        // Trigger download
        window.location.href = '/download_report?include_map=' + mapParam;
    }}
    closeModal();
}}

// Legacy function support if cached
function downloadReport(includeMap) {{
    confirmDownload(includeMap);
}}
</script>
</body>
</html>
"""

def generate_compromised_hosts_html(hosts):
    html = ""
    for host in hosts:
        html += f'''
    <div class="host"><div class="host-ip">{host['ip']}</div><div class="host-service">{host['service']}</div><div class="host-tag tag-owned">{host['tag']}</div></div>
        '''
    return html

def generate_credentials_html(creds):
    html = ""
    for cred in creds:
        status_class = "status-done" if "✓" in cred['status'] else "status-fail" if "✗" in cred['status'] else "status-pending"
        html += f'''
      <tr><td>{cred['source']}</td><td>{cred['credential']}</td><td>{cred['target']}</td><td class="{status_class}">{cred['status']}</td></tr>
        '''
    return html

def main():
    parser = argparse.ArgumentParser(description="Generate infrastructure assessment reports")
    parser.add_argument('--output', default='report.html', help='Output HTML file')
    parser.add_argument('--data', help='JSON file with report data')
    args = parser.parse_args()

    data = DEFAULT_DATA
    if args.data:
        with open(args.data, 'r') as f:
            data = json.load(f)

    # Add dynamic data
    data['current_date'] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    data['num_hosts'] = len(data['compromised_hosts'])
    data['num_creds'] = len(data['credentials'])
    data['compromised_hosts_summary'] = ', '.join([host['ip'] for host in data['compromised_hosts']])

    # Generate dynamic parts
    data['compromised_hosts_html'] = generate_compromised_hosts_html(data['compromised_hosts'])
    data['credentials_html'] = generate_credentials_html(data['credentials'])

    # Render template
    html = HTML_TEMPLATE.format(**data)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report generated: {args.output}")

if __name__ == "__main__":
    main()
