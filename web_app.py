from flask import Flask, request, render_template_string, send_file
import json
from datetime import datetime
import os

app = Flask(__name__)

# HTML Template for the form
FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Generator - Data Input</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --accent-hover: #3fb950;
            --danger-color: #f85149;
            --input-bg: #0d1117;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: var(--bg-color); color: var(--text-color); line-height: 1.6; }
        .container { max-width: 1000px; margin: 40px auto; background: var(--card-bg); padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); border: 1px solid var(--border-color); }
        h1 { color: var(--accent-color); text-align: center; margin-bottom: 40px; font-weight: 300; letter-spacing: 1px; }
        .section { margin-bottom: 40px; padding: 25px; border: 1px solid var(--border-color); border-radius: 8px; background: rgba(255,255,255,0.02); }
        .section h2 { color: var(--text-color); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-top: 0; font-size: 1.2rem; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #8b949e; }
        input, textarea, select { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-color); font-size: 14px; box-sizing: border-box; transition: border-color 0.2s; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: var(--accent-color); }
        .host-entry, .cred-entry, .stat-entry { border: 1px solid var(--border-color); padding: 20px; margin-bottom: 15px; border-radius: 8px; background: rgba(0,0,0,0.2); position: relative; }
        button { background: var(--accent-color); color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; transition: background 0.2s; }
        button:hover { filter: brightness(1.1); }
        .add-btn { background: #238636; width: 100%; margin-top: 10px; }
        .remove-btn { background: var(--danger-color); padding: 8px 16px; font-size: 12px; position: absolute; top: 20px; right: 20px; }
        .submit-btn { width: 100%; background: #238636; margin-top: 20px; font-size: 18px; padding: 15px; }
        .row { display: flex; gap: 20px; }
        .col { flex: 1; }
        small { color: #8b949e; display: block; margin-top: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛠 Report Generator</h1>
        <form method="POST" action="/generate" enctype="multipart/form-data">
            <div class="section">
                <h2>Basic Information</h2>
                <div class="form-group">
                    <label for="title">Report Title:</label>
                    <input type="text" id="title" name="title" placeholder="e.g., Infrastructure Assessment" required>
                </div>
                <div class="form-group">
                    <label for="update_date">Update Date:</label>
                    <input type="text" id="update_date" name="update_date" placeholder="YYYY-MM-DD HH:MM UTC" required>
                </div>
            </div>

            <div class="section">
                <h2>Statistics</h2>
                <div id="stats-container">
                    <!-- Stats will be added here -->
                </div>
                <button type="button" class="add-btn" onclick="addStatistic()">+ Add Statistic</button>
            </div>

            <div class="section">
                <h2>Compromised Hosts</h2>
                <div id="hosts-container">
                    <!-- Hosts will be added here -->
                </div>
                <button type="button" class="add-btn" onclick="addHost()">+ Add Host</button>
            </div>

            <div class="section">
                <h2>Credentials</h2>
                <div id="creds-container">
                    <!-- Credentials will be added here -->
                </div>
                <button type="button" class="add-btn" onclick="addCredential()">+ Add Credential</button>
            </div>
            
            <div class="section">
                 <h2>Markdown Content</h2>
                 <div class="form-group">
                    <label>Additional Markdown Notes:</label>
                    <textarea name="markdown" rows="10" placeholder="# Executive Summary\n\nWrite your report content here..."></textarea>
                 </div>
            </div>

            <button type="submit" class="submit-btn">Generate Report</button>
        </form>
    </div>

    <script>
        // Set default date
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
        document.getElementById('update_date').value = dateStr;

        function addHost() {
            const container = document.getElementById('hosts-container');
            const newEntry = document.createElement('div');
            newEntry.className = 'host-entry';
            newEntry.innerHTML = `
                <div class="row">
                    <div class="col form-group">
                        <label>IP Address:</label>
                        <input type="text" name="host_ip[]" placeholder="e.g. 192.168.1.10" required>
                    </div>
                     <div class="col form-group">
                        <label>Parent/Pivot Host IP (Optional):</label>
                        <input type="text" name="host_parent[]" placeholder="e.g. 10.10.10.5">
                        <small>Leave empty if this is an entry point.</small>
                    </div>
                </div>
                <div class="row">
                    <div class="col form-group">
                        <label>Service Description:</label>
                        <textarea name="host_service[]" rows="2" placeholder="e.g. Apache Tomcat, Running as SYSTEM" required></textarea>
                    </div>
                     <div class="col form-group">
                        <label>Host Type:</label>
                        <select name="host_type[]">
                            <option value="server">Server (Default)</option>
                            <option value="dc">Domain Controller (DC)</option>
                            <option value="db">Database (DB)</option>
                            <option value="webapp">Web App</option>
                            <option value="network">Network Device</option>
                            <option value="workstation">Workstation</option>
                        </select>
                    </div>
                     <div class="col form-group">
                        <label>Host OS:</label>
                        <select name="host_os[]">
                            <option value="linux">Linux</option>
                            <option value="windows">Windows</option>
                            <option value="macos">macOS</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Tag / Status:</label>
                    <input type="text" name="host_tag[]" placeholder="e.g. SYSTEM SHELL" required>
                </div>
                <button type="button" class="remove-btn" onclick="removeEntry(this)">Remove</button>
            `;
            container.appendChild(newEntry);
        }

        function addCredential() {
            const container = document.getElementById('creds-container');
            const newEntry = document.createElement('div');
            newEntry.className = 'cred-entry';
            newEntry.innerHTML = `
                <div class="row">
                    <div class="col form-group">
                        <label>Source:</label>
                        <input type="text" name="cred_source[]" placeholder="e.g. database.config" required>
                    </div>
                    <div class="col form-group">
                        <label>Target:</label>
                        <input type="text" name="cred_target[]" placeholder="e.g. 192.168.1.50 (MySQL)" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Credential:</label>
                    <input type="text" name="cred_credential[]" placeholder="user:password" required>
                </div>
                <div class="form-group">
                    <label>Status:</label>
                    <input type="text" name="cred_status[]" placeholder="e.g. ✓ Valid" value="✓ Valid" required>
                </div>
                <button type="button" class="remove-btn" onclick="removeEntry(this)">Remove</button>
            `;
            container.appendChild(newEntry);
        }

        function removeEntry(button) {
            button.parentElement.remove();
        }

        function addStatistic() {
            const container = document.getElementById('stats-container');
            const newEntry = document.createElement('div');
            newEntry.className = 'stat-entry';
            newEntry.innerHTML = `
                <div class="row">
                    <div class="col form-group">
                        <label>Statistic Name:</label>
                        <input type="text" name="stat_name[]" placeholder="e.g., Subnets Found" required>
                    </div>
                    <div class="col form-group">
                        <label>Value:</label>
                        <input type="text" name="stat_value[]" placeholder="e.g., 5" required>
                    </div>
                </div>
                <button type="button" class="remove-btn" onclick="removeEntry(this)">Remove</button>
            `;
            container.appendChild(newEntry);
        }
        
        // Add initial empty fields
        addHost();
        addCredential();
    </script>
</body>
</html>
"""

REPORT_TEMPLATE_WITH_USERS = """
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

{stats_bar_html}

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
{users_html}

<!-- ═══════════════ ADDITIONAL DATA ═══════════════ -->
{additional_html}

<!-- ═══════════════ MARKDOWN CONTENT ═══════════════ -->
{markdown_html}

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
    if (promptType === 'pdf') {{
        // Open view_report in new tab for printing
        window.open('/view_report?include_map=' + mapParam, '_blank');
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
        html += f"""
    <div class="host"><div class="host-ip">{host['ip']}</div><div class="host-service">{host['service']}</div><div class="host-tag tag-owned">{host['tag']}</div></div>
        """
    return html

def generate_credentials_html(creds):
    html = ""
    for cred in creds:
        status_class = "status-done" if "✓" in cred['status'] else "status-fail" if "✗" in cred['status'] else "status-pending"
        html += f"""
      <tr><td>{cred['source']}</td><td>{cred['credential']}</td><td>{cred['target']}</td><td class="{status_class}">{cred['status']}</td></tr>
        """
    return html

def generate_stats_bar_html(stats):
    html = '<div class="stats-bar">'
    for name, value in stats.items():
        html += f'<div class="stat"><div class="stat-value">{value}</div><div class="stat-label">{name}</div></div>'
    html += '</div>'
    return html

def generate_attack_map_html_from_data(hosts, creds, title, update_date):
    """Generate advanced attack chain map using form data"""
    import json
    import math

    # 1. Process Data
    nodes = []
    edges = []
    zones = {}
    
    # Helper to extract subnet (Zone)
    def get_subnet(ip):
        parts = ip.replace('/',' ').split('.')
        if len(parts) >= 3:
            return f"{parts[0]}.{parts[1]}.{parts[2]}"
        return "external"
        
    # Helper for layout
    def get_zone_id(subnet):
        return "z_" + subnet.replace('.', '_')

    # 1a. Build Nodes
    for i, host in enumerate(hosts):
        ip = host['ip'].strip()
        if not ip: continue
        
        # Heuristics
        service = host['service'].lower()
        tag_list = host['tag'] if isinstance(host['tag'], list) else [host['tag']]
        tag_str = " ".join(str(t) for t in tag_list).lower()
        
        # Zone
        subnet = get_subnet(ip)
        zid = get_zone_id(subnet)
        
        # Type
        n_type = host.get('type', 'server')
        # Fallback if empty
        if not n_type:
             if 'sql' in service or 'db' in service or 'database' in service: n_type = 'db'
             elif 'domain controller' in service or 'dc' in service: n_type = 'dc'
             elif 'web' in service or 'http' in service or 'iis' in service: n_type = 'webapp'
             elif 'firewall' in service or 'router' in service or 'proxy' in service: n_type = 'network'
             elif 'storage' in service or 'nas' in service or 's3' in service: n_type = 'storage'
             else: n_type = 'server'
        
        # OS
        n_os = host.get('os', 'linux')
        if not n_os:
             if 'windows' in service or 'win' in service or 'iis' in service: n_os = 'windows'
             else: n_os = 'linux'
        
        # Sev
        n_sev = 'info'
        if 'owned' in tag_str or 'root' in tag_str: n_sev = 'owned'
        elif 'critical' in tag_str: n_sev = 'critical'
        elif 'high' in tag_str: n_sev = 'high'
        elif 'medium' in tag_str: n_sev = 'medium'
        
        # Ports/Desc
        desc = host['service']
        if tag_str:
            desc += f" [{host['tag']}]"
            
        nodes.append({
            'ip': ip,
            'name': ip, # simplified
            'zone': zid,
            'sev': n_sev,
            'type': n_type,
            'os': n_os,
            'ports': desc,
            'tags': [t.lower() for t in map(str, tag_list) if t] + [n_sev, n_type, n_os]
        })
        
        # Register Zone
        if zid not in zones:
            zones[zid] = {
                'id': zid,
                'label': f"SUBNET {subnet}.0/24",
                'count': 0,
                'nodes': []
            }
        zones[zid]['count'] += 1
        zones[zid]['nodes'].append(ip)

    # 1b. Build Credential Nodes (Zone: "creds")
    if creds:
        zid = 'creds'
        if zid not in zones:
            zones[zid] = {'id': zid, 'label': 'HARVESTED CREDENTIALS', 'count': 0, 'nodes': []}
            
        for i, cred in enumerate(creds):
            nodes.append({
                'ip': f"CRED-{i}",
                'name': cred['source'],
                'zone': zid,
                'sev': 'owned' if '✓' in cred['status'] else 'high',
                'type': 'key',
                'os': '',
                'ports': f"{cred['credential'].replace('<code>','').replace('</code>','')} -> {cred['target']}",
                'tags': ['creds']
            })
            zones[zid]['count'] += 1
            zones[zid]['nodes'].append(f"CRED-{i}")

    # 1c. Build Edges
    for i, host in enumerate(hosts):
        parent = host.get('parent', '').strip()
        if parent:
            ip = host['ip'].strip()
            edges.append({
                'from': parent,
                'to': ip,
                'type': 'owned',
                'label': 'pivot'
            })

    # 2. Zone Layout
    # Grid: 2 columns
    ZONE_W = 550
    ZONE_PADDING = 30
    COL_GAP = 50
    ROW_GAP = 50
    START_X = 50
    START_Y = 100
    
    zone_list = list(zones.values())
    layout_zones = {}
    
    # 2-column flow logic
    col_heights = [START_Y, START_Y]
    
    # Custom sort: put 'creds' last
    zone_list.sort(key=lambda z: 1 if z['id'] == 'creds' else 0)
    
    colors = ['#58a6ff', '#3fb950', '#d29922', '#bc8cff', '#8b949e', '#f85149']
    
    for i, z in enumerate(zone_list):
        # Estimate height: approx 3 nodes per row, 80px per row + padding
        rows_needed = math.ceil(z['count'] / 3.0)
        est_h = (rows_needed * 90) + 60
        if est_h < 150: est_h = 150
        
        # Pick column with smallest height
        col = 0
        if col_heights[1] < col_heights[0]: col = 1
        
        x = START_X + (col * (ZONE_W + COL_GAP))
        y = col_heights[col]
        
        color = colors[i % len(colors)]
        if z['id'] == 'creds': color = '#f85149'
        
        layout_zones[z['id']] = {
            'x': x, 'y': y, 'w': ZONE_W, 'h': est_h, 
            'label': z['label'],
            'color': color
        }
        
        # Update column height
        col_heights[col] += est_h + ROW_GAP

    # 3. Serialization
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    zones_json = json.dumps(layout_zones)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Attack Map - {title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#07090d;color:#b8bcc4;font-family:'DM Sans',sans-serif;overflow:hidden;height:100vh;width:100vw}}
  .scanlines{{position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);pointer-events:none;z-index:999}}
  #canvas-container{{position:absolute;inset:0;overflow:hidden;cursor:grab}}
  #canvas-container.dragging{{cursor:grabbing}}
  #graph-svg{{position:absolute;top:0;left:0;width:100%;height:100%}}
  .hud-top{{position:fixed;top:0;left:0;right:0;z-index:100;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(180deg,rgba(7,9,13,0.97) 0%,rgba(7,9,13,0.8) 70%,transparent 100%);pointer-events:none}}
  .hud-top>*{{pointer-events:auto}}
  .hud-title{{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:#bc8cff;letter-spacing:2px;text-transform:uppercase}}
  .hud-subtitle{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#555;margin-top:2px}}
  .hud-stats{{display:flex;gap:16px}}
  .hud-stat{{text-align:center}}
  .hud-stat-val{{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:#4dabf7}}
  .hud-stat-lbl{{font-size:8px;color:#555;text-transform:uppercase;letter-spacing:1px}}
  .filter-bar{{position:fixed;top:52px;left:50%;transform:translateX(-50%);z-index:100;display:flex;gap:3px;background:rgba(13,17,23,0.92);border:1px solid #21262d;border-radius:8px;padding:3px}}
  .filter-btn{{background:transparent;border:1px solid transparent;color:#8b949e;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:5px 10px;border-radius:6px;cursor:pointer;letter-spacing:0.5px;transition:all .2s}}
  .filter-btn:hover{{color:#c9d1d9;background:rgba(255,255,255,0.04)}}
  .filter-btn.active{{background:#bc8cff22;color:#bc8cff;border-color:#bc8cff44}}
  .tooltip{{position:fixed;z-index:200;background:rgba(13,17,23,0.96);border:1px solid #30363d;border-radius:6px;padding:10px 14px;max-width:400px;pointer-events:none;opacity:0;transition:opacity .15s;backdrop-filter:blur(8px);font-family:'IBM Plex Mono',monospace}}
  .tooltip-title{{font-size:11px;font-weight:600;color:#c9d1d9;margin-bottom:4px}}
  .tooltip-service{{font-size:9px;color:#8b949e;line-height:1.5}}
  .tooltip-tag{{display:inline-block;font-size:8px;font-weight:600;padding:2px 6px;border-radius:3px;margin-top:6px;letter-spacing:0.5px}}
  .tooltip-tag.critical{{background:rgba(248,81,73,0.2);color:#f85149}}
  .tooltip-tag.high{{background:rgba(210,153,34,0.2);color:#d29922}}
  .tooltip-tag.owned{{background:rgba(188,140,255,0.2);color:#bc8cff}}
  .tooltip-tag.medium{{background:rgba(63,185,80,0.2);color:#3fb950}}
  .tooltip-tag.info{{background:rgba(88,166,255,0.2);color:#58a6ff}}
  .tooltip-tag.tried{{background:rgba(139,148,158,0.2);color:#8b949e;text-decoration:line-through}}
  .hud-controls{{position:fixed;bottom:20px;right:20px;z-index:100;display:flex;flex-direction:column;gap:4px}}
  .hud-controls button{{width:32px;height:32px;background:rgba(13,17,23,0.9);border:1px solid #21262d;border-radius:6px;color:#8b949e;font-size:16px;cursor:pointer;font-family:'IBM Plex Mono',monospace;display:flex;align-items:center;justify-content:center}}
  .hud-controls button:hover{{border-color:#bc8cff44;color:#bc8cff}}
  .search-box{{position:fixed;top:52px;right:20px;z-index:100}}
  .search-box input{{background:rgba(13,17,23,0.92);border:1px solid #21262d;border-radius:6px;padding:5px 10px;color:#c9d1d9;font-family:'IBM Plex Mono',monospace;font-size:9px;width:160px;outline:none}}
  .search-box input:focus{{border-color:#bc8cff44}}
  .node-group{{transition:opacity .3s}}
  .node-group.dimmed{{opacity:0.08}}
  .node-group:hover{{filter:brightness(1.3)}}
  @keyframes glowPulse{{0%,100%{{opacity:0.15}}50%{{opacity:0.45}}}}
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="hud-top">
  <div>
    <div class="hud-title">⚠️ ATTACK CHAIN — {title}</div>
    <div class="hud-subtitle">{len(hosts)} hosts │ {len(creds)} creds │ Updated: {update_date}</div>
  </div>
  <div class="hud-stats">
    <div class="hud-stat"><div class="hud-stat-val">{len(zones)}</div><div class="hud-stat-lbl">Subnets</div></div>
    <div class="hud-stat"><div class="hud-stat-val">{len(hosts)}</div><div class="hud-stat-lbl">Hosts</div></div>
    <div class="hud-stat"><div class="hud-stat-val">{len(creds)}</div><div class="hud-stat-lbl">Creds</div></div>
  </div>
</div>
<div class="filter-bar">
  <button class="filter-btn active" data-filter="all">ALL</button>
  <button class="filter-btn" data-filter="owned">OWNED</button>
  <button class="filter-btn" data-filter="dc">DCs</button>
  <button class="filter-btn" data-filter="db">DATABASES</button>
  <button class="filter-btn" data-filter="windows">WINDOWS</button>
  <button class="filter-btn" data-filter="linux">LINUX</button>
  <button class="filter-btn" data-filter="webapp">WEB APPS</button>
  <button class="filter-btn" data-filter="creds">CREDS</button>
</div>
<div class="search-box"><input type="text" id="search" placeholder="Search host..."></div>
<div id="canvas-container"><svg id="graph-svg"></svg></div>
<div class="tooltip" id="tooltip">
  <div class="tooltip-title" id="tt-title"></div>
  <div class="tooltip-service" id="tt-service"></div>
  <span class="tooltip-tag" id="tt-tag"></span>
</div>
<div class="hud-controls">
  <button id="zoom-in">+</button>
  <button id="zoom-out">−</button>
  <button id="zoom-fit">⊡</button>
</div>

<script>
const container = document.getElementById("canvas-container");
const svg = document.getElementById("graph-svg");
let viewBox = {{x:-50, y:-20, w:2200, h:1900}};
let isDragging = false, dragStart = {{}}, viewStart = {{}};

function updateViewBox() {{
  svg.setAttribute("viewBox", `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.w}} ${{viewBox.h}}`);
}}

// ═══════════════ DATA ═══════════════
const ZONES = {zones_json};
const NODES = {nodes_json};
const EDGES = {edges_json};

// ═══════════════ LAYOUT ═══════════════
function layoutNodes() {{
  const zoneNodes = {{}};
  for (const n of NODES) {{
    if (!zoneNodes[n.zone]) zoneNodes[n.zone] = [];
    zoneNodes[n.zone].push(n);
  }}
  for (const [zid, nodes] of Object.entries(zoneNodes)) {{
    const z = ZONES[zid];
    if (!z) continue;
    
    // Grid layout inside zone
    const cols = 3;
    const cellW = 120; // Approx width per node
    const cellH = 90;
    
    nodes.forEach((n, i) => {{
      const col = i % cols;
      const row = Math.floor(i / cols);
      // Center in zone
      // Start position?
      n.x = z.x + 60 + (col * 140);
      n.y = z.y + 60 + (row * 90);
    }});
  }}
}}

// ═══════════════ ICONS ═══════════════
function nodeIcon(type, color, sz) {{
  const s = sz || 10;
  const h = s * 0.7;
  switch(type) {{
    case "dc":
      return `<rect x="${{-s}}" y="${{-h}}" width="${{s*2}}" height="${{h*2}}" rx="2" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{-s+3}}" y1="${{-h+4}}" x2="${{s-3}}" y2="${{-h+4}}" stroke="${{color}}" stroke-width="0.8"/>` +
             `<line x1="${{-s+3}}" y1="${{-h+8}}" x2="${{s-3}}" y2="${{-h+8}}" stroke="${{color}}" stroke-width="0.8"/>` +
             `<text x="0" y="${{h+8}}" font-size="5" fill="${{color}}" text-anchor="middle" font-family="IBM Plex Mono">DC</text>`;
    case "db":
      return `<ellipse cx="0" cy="${{-h+3}}" rx="${{s-2}}" ry="3" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{-s+2}}" y1="${{-h+3}}" x2="${{-s+2}}" y2="${{h-3}}" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{s-2}}" y1="${{-h+3}}" x2="${{s-2}}" y2="${{h-3}}" stroke="${{color}}" stroke-width="1.2"/>` +
             `<ellipse cx="0" cy="${{h-3}}" rx="${{s-2}}" ry="3" fill="none" stroke="${{color}}" stroke-width="1.2"/>`;
    case "webapp":
      return `<rect x="${{-s}}" y="${{-h}}" width="${{s*2}}" height="${{h*1.6}}" rx="2" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{-s}}" y1="${{-h+4}}" x2="${{s}}" y2="${{-h+4}}" stroke="${{color}}" stroke-width="0.6"/>` +
             `<circle cx="${{-s+3}}" cy="${{-h+2}}" r="0.8" fill="${{color}}"/>` +
             `<circle cx="${{-s+5.5}}" cy="${{-h+2}}" r="0.8" fill="${{color}}"/>`;
    case "network":
      return `<circle cx="0" cy="0" r="${{s-2}}" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="0" y1="${{-s+4}}" x2="0" y2="${{s-4}}" stroke="${{color}}" stroke-width="0.7"/>` +
             `<line x1="${{-s+4}}" y1="0" x2="${{s-4}}" y2="0" stroke="${{color}}" stroke-width="0.7"/>`;
    case "storage":
      return `<rect x="${{-s}}" y="${{-h}}" width="${{s*2}}" height="${{h*2}}" rx="1" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{-s+2}}" y1="0" x2="${{s-2}}" y2="0" stroke="${{color}}" stroke-width="0.6"/>` +
             `<circle cx="${{s-4}}" cy="${{-h/2}}" r="1" fill="${{color}}"/>` +
             `<circle cx="${{s-4}}" cy="${{h/2}}" r="1" fill="${{color}}"/>`;
    case "key":
      return `<circle cx="0" cy="-2" r="4" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="0" y1="2" x2="0" y2="8" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="0" y1="6" x2="3" y2="6" stroke="${{color}}" stroke-width="1"/>`;
    default:
      return `<rect x="${{-s}}" y="${{-h}}" width="${{s*2}}" height="${{h*2}}" rx="2" fill="none" stroke="${{color}}" stroke-width="1.2"/>` +
             `<line x1="${{-s+3}}" y1="${{-h+5}}" x2="${{s-3}}" y2="${{-h+5}}" stroke="${{color}}" stroke-width="0.6"/>` +
             `<line x1="${{-s+3}}" y1="${{-h+9}}" x2="${{s-3}}" y2="${{-h+9}}" stroke="${{color}}" stroke-width="0.6"/>`;
  }}
}}

const SEV_COLORS = {{
  "owned":"#bc8cff","critical":"#f85149","high":"#d29922",
  "medium":"#3fb950","info":"#58a6ff","low":"#484f58","tried":"#555"
}};

// ═══════════════ RENDER ═══════════════
function render() {{
  layoutNodes();
  let html = '<defs>';
  html += '<filter id="glow"><feGaussianBlur stdDeviation="3" result="c"/><feMerge><feMergeNode in="c"/><feMergeNode in="SourceGraphic"/></feMerge></filter>';
  html += '</defs>';

  // Draw zones
  for (const [zid, z] of Object.entries(ZONES)) {{
    const c = z.color || "#21262d";
    html += `<rect x="${{z.x}}" y="${{z.y}}" width="${{z.w}}" height="${{z.h}}" rx="6" fill="rgba(13,17,23,0.6)" stroke="${{c}}33" stroke-width="1"/>`;
    html += `<text x="${{z.x+10}}" y="${{z.y+16}}" font-size="8" fill="${{c}}" font-family="IBM Plex Mono" font-weight="600" letter-spacing="1" opacity="0.8">${{z.label}}</text>`;
    // Subtle bg glow
    html += `<rect x="${{z.x}}" y="${{z.y}}" width="${{z.w}}" height="${{z.h}}" rx="6" fill="${{c}}" opacity="0.02"/>`;
  }}

  // Draw edges
  for (const e of EDGES) {{
    const fromN = NODES.find(n => n.ip === e.from);
    const toN = NODES.find(n => n.ip === e.to);
    if (!fromN || !toN || !fromN.x || !toN.x) continue;
    const color = e.type === "owned" ? "#bc8cff" : e.type === "auth" ? "#f85149" : "#21262d";
    const dash = e.type === "auth" ? 'stroke-dasharray="4,3"' : '';
    const opacity = e.type === "normal" ? "0.3" : "0.5";
    const mx = (fromN.x + toN.x) / 2;
    const my = (fromN.y + toN.y) / 2;
    const cx = mx + (toN.y - fromN.y) * 0.15;
    const cy = my - (toN.x - fromN.x) * 0.15;
    html += `<path d="M${{fromN.x}},${{fromN.y}} Q${{cx}},${{cy}} ${{toN.x}},${{toN.y}}" fill="none" stroke="${{color}}" stroke-width="0.8" ${{dash}} opacity="${{opacity}}"/>`;
    // Arrowhead logic? for now just lines
  }}

  // Draw nodes
  for (const n of NODES) {{
    if (!n.x) continue;
    const color = SEV_COLORS[n.sev] || "#58a6ff";
    const isOwned = n.sev === "owned";
    const filterAttr = isOwned ? 'filter="url(#glow)"' : '';

    html += `<g class="node-group" data-ip="${{n.ip}}" data-name="${{n.name}}" data-severity="${{n.sev}}" data-tags="${{(n.tags||[]).join(',')}}" data-os="${{n.os||''}}" data-zone="${{n.zone}}" transform="translate(${{n.x}},${{n.y}})" ${{filterAttr}}
      onmouseover="showTip(event,'${{n.ip.replace(/'/g,"\\'")}}','${{n.name.replace(/'/g,"\\'")}}','${{n.ports.replace(/'/g,"\\'")}}','${{n.sev}}')"
      onmouseout="hideTip()">`;

    // Pulse for owned
    if (isOwned) {{
      html += `<circle r="14" fill="${{color}}" opacity="0.1" style="animation:glowPulse 2s infinite"/>`;
    }}

    html += nodeIcon(n.type, color, 10);
    html += `<text x="0" y="15" font-size="5" fill="${{color}}" text-anchor="middle" font-family="IBM Plex Mono" font-weight="500" opacity="0.9">${{n.name.length > 14 ? n.name.slice(0,12) + '..' : n.name}}</text>`;
    html += `<text x="0" y="20" font-size="4" fill="#555" text-anchor="middle" font-family="IBM Plex Mono">${{n.ip}}</text>`;

    if (n.tags && n.tags.includes("creds")) {{
      html += `<text x="8" y="-6" font-size="6" fill="#d29922">🔑</text>`;
    }}
    html += `</g>`;
  }}

  svg.innerHTML = html;
  // Fit view roughly?
  updateViewBox();
}}

// ═══════════════ INTERACTION ═══════════════
function showTip(e, ip, name, ports, sev) {{
  const tt = document.getElementById("tooltip");
  document.getElementById("tt-title").textContent = `${{name}} — ${{ip}}`;
  document.getElementById("tt-service").textContent = ports;
  const tag = document.getElementById("tt-tag");
  tag.textContent = sev.toUpperCase();
  tag.className = `tooltip-tag ${{sev}}`;
  tt.style.opacity = 1;
  tt.style.left = (e.clientX + 16) + "px";
  tt.style.top = (e.clientY - 10) + "px";
}}
function hideTip() {{ document.getElementById("tooltip").style.opacity = 0; }}

// Pan
container.addEventListener("mousedown", e => {{
  isDragging = true; container.classList.add("dragging");
  dragStart = {{x:e.clientX, y:e.clientY}};
  viewStart = {{x:viewBox.x, y:viewBox.y}};
}});
window.addEventListener("mousemove", e => {{
  if (!isDragging) return;
  const scale = viewBox.w / container.clientWidth;
  viewBox.x = viewStart.x - (e.clientX - dragStart.x) * scale;
  viewBox.y = viewStart.y - (e.clientY - dragStart.y) * scale;
  updateViewBox();
}});
window.addEventListener("mouseup", () => {{ isDragging = false; container.classList.remove("dragging"); }});

// Zoom
container.addEventListener("wheel", e => {{
  e.preventDefault();
  const factor = e.deltaY > 0 ? 1.08 : 0.93;
  const rect = container.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;
  const my = (e.clientY - rect.top) / rect.height;
  const nw = viewBox.w * factor, nh = viewBox.h * factor;
  viewBox.x += (viewBox.w - nw) * mx;
  viewBox.y += (viewBox.h - nh) * my;
  viewBox.w = nw; viewBox.h = nh;
  updateViewBox();
}}, {{passive:false}});

document.getElementById("zoom-in").onclick = () => {{
  const cx = viewBox.x+viewBox.w/2, cy = viewBox.y+viewBox.h/2;
  viewBox.w *= 0.8; viewBox.h *= 0.8;
  viewBox.x = cx-viewBox.w/2; viewBox.y = cy-viewBox.h/2;
  updateViewBox();
}};
document.getElementById("zoom-out").onclick = () => {{
  const cx = viewBox.x+viewBox.w/2, cy = viewBox.y+viewBox.h/2;
  viewBox.w *= 1.25; viewBox.h *= 1.25;
  viewBox.x = cx-viewBox.w/2; viewBox.y = cy-viewBox.h/2;
  updateViewBox();
}};
document.getElementById("zoom-fit").onclick = () => {{
  viewBox = {{x:-50, y:-20, w:2200, h:1900}};
  updateViewBox();
}};

// ═══════════════ FILTERS ═══════════════
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    document.querySelectorAll('.node-group').forEach(g => {{
      const tags = g.dataset.tags || '';
      const os = g.dataset.os || '';
      const zone = g.dataset.zone || '';
      let show = true;
      if (f === "dc") show = tags.includes("dc");
      else if (f === "db") show = tags.includes("db");
      else if (f === "windows") show = os === "windows";
      else if (f === "linux") show = os === "linux";
      else if (f === "webapp") show = tags.includes("webapp");
      else if (f === "owned") show = tags.includes("owned");
      else if (f === "creds") show = tags.includes("creds");
      g.classList.toggle("dimmed", !show);
    }});
  }});
}});

// Search
document.getElementById("search").addEventListener("input", e => {{
  const q = e.target.value.toLowerCase();
  if (!q) {{
    document.querySelectorAll('.node-group').forEach(g => g.classList.remove('dimmed'));
    return;
  }}
  document.querySelectorAll('.node-group').forEach(g => {{
    const match = (g.dataset.ip + g.dataset.name + g.dataset.tags).toLowerCase().includes(q);
    g.classList.toggle("dimmed", !match);
  }});
}});

render();
</script>
</body>
</html>"""

    # Helper to extract subnet
    def get_subnet(ip):
        parts = ip.replace('/',' ').split('.')
        if len(parts) >= 3:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return "External / Unknown"

    # First pass: Create nodes and group by subnet
    for i, host in enumerate(hosts):
        ip_clean = host['ip'].split()[0]
        subnet = get_subnet(ip_clean)
        
        node = {
            'id': i,
            'type': 'host',
            'name': host['ip'],
            'clean_ip': ip_clean,
            'parent_ip': host.get('parent', '').strip(),
            'description': host['service'],
            'tag': host['tag'],
            'subnet': subnet,
            'x': 0, 'y': 0 # To be calculated
        }
        nodes.append(node)
        
        if subnet not in subnets:
            subnets[subnet] = []
        subnets[subnet].append(node)

    # 2. Layout Calculation
    subnet_boxes = []
    
    # Config
    start_x, start_y = 100, 150
    subnet_width = 350
    host_spacing_x = 80
    host_spacing_y = 100
    padding = 60
    subnet_gap = 100
    max_row_width = 1600

    current_x = start_x
    current_y = start_y
    
    for subnet_name, snippet_nodes in subnets.items():
        # Determine box size
        hosts_per_row = 3
        num_rows = math.ceil(len(snippet_nodes) / hosts_per_row)
        
        box_w = (hosts_per_row * host_spacing_x) + (padding * 2) - host_spacing_x + 50
        box_h = (num_rows * host_spacing_y) + padding + 40
        
        # Check if we need to wrap to next row
        if current_x + box_w > max_row_width:
            current_x = start_x
            current_y += 500 # Move down significantly
            
        subnet_box = {
            'name': subnet_name,
            'x': current_x, 
            'y': current_y,
            'w': box_w,
            'h': box_h
        }
        subnet_boxes.append(subnet_box)
        
        # Position nodes inside box
        for idx, node in enumerate(snippet_nodes):
            r = idx // hosts_per_row
            c = idx % hosts_per_row
            
            node['x'] = current_x + padding + (c * host_spacing_x)
            node['y'] = current_y + padding + 40 + (r * host_spacing_y)
            
        current_x += box_w + subnet_gap

    # 3. Create Links (Host -> Host)
    for node in nodes:
        if node['parent_ip']:
            # Find parent node
            for candidate in nodes:
                # Match by clean IP or if parent IP is contained in candidate name
                if candidate['clean_ip'] == node['parent_ip'] or node['parent_ip'] in candidate['name']:
                    links.append({
                        'source': candidate, # store ref for now
                        'target': node,
                        'type': 'pivot'
                    })
                    break

    # 4. Credential Nodes
    cred_start_y = current_y + 400 # Below the last subnet row
    cred_start_x = 100
    
    cred_nodes = []
    for i, cred in enumerate(creds):
        node = {
            'id': len(nodes) + i,
            'type': 'cred',
            'name': cred['source'],
            'description': f"{cred['credential']} -> {cred['target']}",
            'tag': 'credential',
            'x': cred_start_x + (i % 5) * 250,
            'y': cred_start_y + (i // 5) * 120
        }
        cred_nodes.append(node)
        nodes.append(node)

    # Finalize Links (replace object refs with coords or IDs if needed, but for JS we render lines based on coords)
    # Actually, let's prepare simple link data for JS: {x1, y1, x2, y2}
    js_links = []
    for link in links:
        js_links.append({
            'x1': link['source']['x'],
            'y1': link['source']['y'],
            'x2': link['target']['x'],
            'y2': link['target']['y']
        })

    # Serialize for JS
    nodes_json = json.dumps(nodes)
    subnets_json = json.dumps(subnet_boxes)
    links_json = json.dumps(js_links)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Attack Chain Map - {{ title }}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#07090d;color:#b8bcc4;font-family:'DM Sans',sans-serif;overflow:hidden;height:100vh;width:100vw}}
  .scanlines{{position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);pointer-events:none;z-index:999}}
  #canvas-container{{position:absolute;inset:0;overflow:hidden;cursor:grab;user-select:none}}
  #canvas-container.dragging{{cursor:grabbing}}
  #graph-svg{{position:absolute;top:0;left:0;width:100%;height:100%}}
  .hud-top{{position:fixed;top:0;left:0;right:0;z-index:100;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(180deg,rgba(7,9,13,0.97) 0%,rgba(7,9,13,0.8) 70%,transparent 100%);pointer-events:none}}
  .hud-top>*{{pointer-events:auto}}
  .hud-title{{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:#f85149;letter-spacing:2px;text-transform:uppercase}}
  .hud-subtitle{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#555;margin-top:2px}}
  .tooltip{{position:fixed;z-index:200;background:rgba(13,17,23,0.96);border:1px solid #30363d;border-radius:6px;padding:10px 14px;max-width:300px;pointer-events:none;opacity:0;transition:opacity .15s;backdrop-filter:blur(8px);font-family:'IBM Plex Mono',monospace}}
  .tooltip-title{{font-size:11px;font-weight:600;color:#c9d1d9;margin-bottom:4px}}
  .tooltip-desc{{font-size:9px;color:#8b949e;line-height:1.5}}
  .hud-controls{{position:fixed;bottom:20px;right:20px;z-index:100;display:flex;flex-direction:column;gap:4px}}
  .hud-controls button{{width:32px;height:32px;background:rgba(13,17,23,0.9);border:1px solid #21262d;border-radius:6px;color:#8b949e;font-size:16px;cursor:pointer;font-family:'IBM Plex Mono',monospace;display:flex;align-items:center;justify-content:center}}
  .hud-controls button:hover{{border-color:#f8514444;color:#f85149}}
  .node-group{{transition:opacity .3s;cursor:pointer}}
  .node-group:hover circle{{filter:brightness(1.5)}}
  .link-line {{stroke: #f85149; stroke-width: 2; fill: none; stroke-opacity: 0.6; stroke-dasharray: 4; transition: opacity 0.3s, stroke-width 0.3s; cursor: pointer; animation: dash 1s linear infinite;}}
  .link-line.dimmed {{ opacity: 0.1; }}
  .link-line:hover {{ opacity: 1 !important; stroke-width: 3; filter: drop-shadow(0 0 5px #f85149); }}
  @keyframes dash {{ to {{ stroke-dashoffset: -8; }} }}
  .subnet-rect {{ fill: rgba(22, 27, 34, 0.4); stroke: #30363d; stroke-width: 1; rx: 8; }}
  .subnet-label {{ fill: #8b949e; font-family: 'IBM Plex Mono'; font-size: 10px; opacity: 0.7; }}
  .link-line { transition: opacity 0.3s, stroke-width 0.3s; cursor: pointer; }
  .link-line.dimmed { opacity: 0.1; }
  .link-line:hover { opacity: 1 !important; stroke-width: 3; filter: drop-shadow(0 0 5px #f85149); }
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="hud-top">
  <div>
    <div class="hud-title">⚠️ ATTACK CHAIN — {title}</div>
    <div class="hud-subtitle">Hosts: {len(hosts)} | Creds: {len(creds)} | Updated: {update_date}</div>
  </div>
</div>
<div id="canvas-container">
    <svg id="graph-svg">
        <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#f85149" />
            </marker>
             <filter id="glow"><feGaussianBlur stdDeviation="2" result="c"/><feMerge><feMergeNode in="c"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <g id="layer-subnets"></g>
        <g id="layer-links"></g>
        <g id="layer-nodes"></g>
    </svg>
</div>
<div class="tooltip" id="tooltip">
  <div class="tooltip-title" id="tt-title"></div>
  <div class="tooltip-desc" id="tt-desc"></div>
</div>
<div class="hud-controls">
  <button id="zoom-in" title="Zoom In">+</button>
  <button id="zoom-out" title="Zoom Out">−</button>
  <button id="zoom-fit" title="Fit to Screen">⊡</button>
</div>

<script>
const container = document.getElementById("canvas-container");
const svg = document.getElementById("graph-svg");
const layerSubnets = document.getElementById("layer-subnets");
const layerLinks = document.getElementById("layer-links");
const layerNodes = document.getElementById("layer-nodes");

const nodes = {nodes_json};
const subnets = {subnets_json};
const links = {links_json};

let viewBox = {{x: 0, y: 0, w: 1600, h: 900}};
let isDragging = false;
let dragStart = {{}};
let viewStart = {{}};

function updateViewBox() {{
  svg.setAttribute("viewBox", `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.w}} ${{viewBox.h}}`);
}}

function render() {{
  // 1. Render Subnets
  let subnetsHtml = '';
  subnets.forEach(s => {{
      subnetsHtml += `<rect class="subnet-rect" x="${{s.x}}" y="${{s.y}}" width="${{s.w}}" height="${{s.h}}"/>`;
      subnetsHtml += `<text class="subnet-label" x="${{s.x+10}}" y="${{s.y+20}}">${{s.name}}</text>`;
  }});
  layerSubnets.innerHTML = subnetsHtml;

  // 2. Render Links
  let linksHtml = '';
  links.forEach(l => {{
      linksHtml += `<line class="link-line" x1="${{l.x1}}" y1="${{l.y1}}" x2="${{l.x2}}" y2="${{l.y2}}" marker-end="url(#arrow)"
        onmouseover="highlightLine(this)" onmouseout="resetLines()"/>`;
  }});
  layerLinks.innerHTML = linksHtml;

  // 3. Render Nodes
  let nodesHtml = '';
  nodes.forEach(n => {{
    const color = n.type === 'host' ? '#f85149' : '#58a6ff';
    nodesHtml += `<g class="node-group" transform="translate(${{n.x}},${{n.y}})"
      onmouseover="showTip(event, '${{n.name}}', '${{n.description.replace(/'/g, "\\'")}}')"
      onmouseout="hideTip()">`;
    
    nodesHtml += `<circle cx="0" cy="0" r="12" fill="${{color}}22" stroke="${{color}}" stroke-width="1.5"/>`;
    nodesHtml += `<circle cx="0" cy="0" r="8" fill="${{color}}" opacity="0.8"/>`;
    nodesHtml += `<text x="0" y="24" font-size="9" fill="${{color}}" text-anchor="middle" font-family="IBM Plex Mono">${{n.clean_ip || n.name}}</text>`;
    nodesHtml += `</g>`;
  }});
  layerNodes.innerHTML = nodesHtml;
  
  updateViewBox();
}}

// ... Mouse Interaction Code (same as before) ...
function showTip(e, name, desc) {{
  const tt = document.getElementById("tooltip");
  document.getElementById("tt-title").textContent = name;
  document.getElementById("tt-desc").innerHTML = desc; // Allow HTML
  tt.style.opacity = 1;
  tt.style.left = (e.clientX + 16) + "px";
  tt.style.top = (e.clientY - 10) + "px";
}}

function hideTip() {{
  document.getElementById("tooltip").style.opacity = 0;
}}

// PAN: Only on LEFT mouse button drag
container.addEventListener("mousedown", e => {{
  if (e.button !== 0) return; // Only left mouse button
  isDragging = true;
  container.classList.add("dragging");
  dragStart = {{x: e.clientX, y: e.clientY}};
  viewStart = {{x: viewBox.x, y: viewBox.y}};
}});

window.addEventListener("mousemove", e => {{
  if (!isDragging) return;
  const scale = viewBox.w / container.clientWidth;
  viewBox.x = viewStart.x - (e.clientX - dragStart.x) * scale;
  viewBox.y = viewStart.y - (e.clientY - dragStart.y) * scale;
  updateViewBox();
}});

window.addEventListener("mouseup", () => {{
  isDragging = false;
  container.classList.remove("dragging");
}});

// ZOOM
container.addEventListener("wheel", e => {{
  e.preventDefault();
  const factor = e.deltaY > 0 ? 1.1 : 0.9;
  const rect = container.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;
  const my = (e.clientY - rect.top) / rect.height;
  const nw = viewBox.w * factor;
  const nh = viewBox.h * factor;
  viewBox.x += (viewBox.w - nw) * mx;
  viewBox.y += (viewBox.h - nh) * my;
  viewBox.w = nw;
  viewBox.h = nh;
  updateViewBox();
}}, {{passive: false}});

// Zoom buttons
document.getElementById("zoom-in").onclick = () => {{
  viewBox.w *= 0.8; viewBox.h *= 0.8; updateViewBox();
}};
document.getElementById("zoom-out").onclick = () => {{
  viewBox.w *= 1.25; viewBox.h *= 1.25; updateViewBox();
}};
document.getElementById("zoom-fit").onclick = () => {{
  // Reset view
  viewBox = {{x: 0, y: 0, w: 1600, h: 900}};
  updateViewBox();
}};

render();
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(FORM_HTML)

@app.route('/generate', methods=['POST'])
def generate():
    # Collect form data
    data = {
        'title': request.form['title'],
        'update_date': request.form['update_date'],
        'stats': {},
        'compromised_hosts': [],
        'credentials': []
    }

    # Collect statistics
    stat_names = request.form.getlist('stat_name[]')
    stat_values = request.form.getlist('stat_value[]')
    
    for i in range(len(stat_names)):
        if stat_names[i]:  # Only add non-empty stats
            data['stats'][stat_names[i]] = stat_values[i] if i < len(stat_values) else ''

    # Collect hosts
    host_ips = request.form.getlist('host_ip[]')
    host_parents = request.form.getlist('host_parent[]')
    host_services = request.form.getlist('host_service[]')
    host_tags = request.form.getlist('host_tag[]')
    host_types = request.form.getlist('host_type[]')
    host_os = request.form.getlist('host_os[]')

    for i in range(len(host_ips)):
        service = host_services[i]
        # Auto-format service description
        if 'ROOT' in service.upper():
            service = service.replace('ROOT', '<b>ROOT</b>', 1)
        
        parent = host_parents[i] if i < len(host_parents) else ''
        h_type = host_types[i] if i < len(host_types) else 'server'
        h_os = host_os[i] if i < len(host_os) else 'linux'
        
        data['compromised_hosts'].append({
            'ip': host_ips[i],
            'parent': parent,
            'service': service,
            'tag': host_tags[i],
            'type': h_type,
            'os': h_os
        })

    # Collect credentials
    cred_sources = request.form.getlist('cred_source[]')
    cred_credentials = request.form.getlist('cred_credential[]')
    cred_targets = request.form.getlist('cred_target[]')
    cred_statuses = request.form.getlist('cred_status[]')

    for i in range(len(cred_sources)):
        credential = cred_credentials[i]
        # Auto-format credential with <code> tags
        formatted_credential = f"<code>{credential}</code>"
        data['credentials'].append({
            'source': cred_sources[i],
            'credential': formatted_credential,
            'target': cred_targets[i],
            'status': cred_statuses[i]
        })

    # Generate summary
    compromised_hosts_summary = ', '.join([host['ip'].split(' ')[0] for host in data['compromised_hosts']])

    # Add dynamic data
    data['current_date'] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    data['num_hosts'] = len(data['compromised_hosts'])
    data['num_creds'] = len(data['credentials'])
    data['compromised_hosts_summary'] = compromised_hosts_summary

    # Initialize optional fields
    data['users'] = []
    data['additional_data'] = []
    data['markdown'] = request.form.get('markdown', '')

    # Generate HTML parts
    data['compromised_hosts_html'] = generate_compromised_hosts_html(data['compromised_hosts'])
    data['credentials_html'] = generate_credentials_html(data['credentials'])
    data['stats_bar_html'] = generate_stats_bar_html(data['stats'])
    data['users_html'] = generate_users_html(data['users'])
    data['additional_html'] = generate_additional_html(data['additional_data'])
    data['markdown_html'] = markdown_to_html(data['markdown'])

    html = REPORT_TEMPLATE_WITH_USERS.format(**data)

    # Save to file
    with open('generated_report.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Generate and save attack map
    attack_map_html = generate_attack_map_html_from_data(
        data['compromised_hosts'],
        data['credentials'],
        data['title'],
        data['update_date']
    )
    with open('attack_map.html', 'w', encoding='utf-8') as f:
        f.write(attack_map_html)

    # Return HTML with link to attack map and clean downloads
    return html + f"""
    <div style="position:fixed;bottom:20px;left:20px;z-index:1000;background:#161B22;border:1px solid #BC8CFF;border-radius:8px;padding:15px;font-family:monospace;font-size:12px;box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
        <div style="color:#BC8CFF;margin-bottom:10px;font-weight:bold;">📊 Report Generated!</div>
        <div style="display:flex;gap:8px;">
            <a href="/attack_map" target="_blank" style="color:#58A6FF;text-decoration:none;display:inline-block;padding:8px 12px;background:#21262D;border-radius:4px;border:1px solid #30363D;">View Attack Map →</a>
            <button onclick="showDownloadModal('html')" style="color:#3FB950;text-decoration:none;display:inline-block;padding:8px 12px;background:#21262D;border-radius:4px;border:1px solid #30363D;cursor:pointer;border:1px solid #3FB950;">Download HTML</button>
            <button onclick="showDownloadModal('pdf')" style="color:#c9d1d9;padding:8px 12px;background:#21262D;border-radius:4px;border:1px solid #30363D;cursor:pointer;">🖨 Save PDF</button>
        </div>
        <style>@media print {{ div[style*="position:fixed"] {{ display: none !important; }} }}</style>
    </div>
    """

@app.route('/download_report')
def download_report():
    """Serve the clean generated report HTML"""
    try:
        report_path = 'generated_report.html'
        include_map = request.args.get('include_map', '1') == '1'
        
        if not include_map:
            return send_file(report_path, as_attachment=True, download_name='report.html')
            
        # If map is included, we verify if map exists
        if os.path.exists('attack_map.html'):
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open('attack_map.html', 'r', encoding='utf-8') as f:
                map_content = f.read()
                
            # Embed map in an iframe with a dedicated header bar (no overlap)
            map_html = f'''
            <div class="map-container" style="margin-top: 40px; border: 1px solid #30363D; border-radius: 8px; overflow: hidden; height: 900px; display: flex; flex-direction: column; page-break-before: always;">
                <div style="background: #161B22; padding: 12px 16px; border-bottom: 1px solid #30363D; font-family: 'Space Grotesk', sans-serif; font-size: 13px; color: #BC8CFF; font-weight: bold; display: flex; align-items: center; gap: 8px;">
                    <span>⚠️ INTERACTIVE ATTACK MAP</span>
                </div>
                <iframe srcdoc="{map_content.replace('"', '&quot;')}" style="width: 100%; height: 100%; border: none; flex: 1; background: #07090d;"></iframe>
            </div>
            '''
            
            # Inject before footer
            content = content.replace('<div class="footer-note">', map_html + '<div class="footer-note">')
            
            # Save temporary bundled file
            bundled_path = 'bundled_report.html'
            with open(bundled_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return send_file(bundled_path, as_attachment=True, download_name='report_with_map.html')
            
        return send_file(report_path, as_attachment=True, download_name='report.html')
    except Exception as e:
        return f"Error downloading report: {str(e)}", 404

@app.route('/view_report')
def view_report():
    """Serve the report inline for printing (PDF generation)"""
    try:
        # Re-use logic from download_report (could be refactored, but keeping it simple)
        report_path = 'generated_report.html'
        include_map = request.args.get('include_map', '1') == '1'

        if not include_map:
             with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Add print script to auto-trigger print dialog
                content += '<script>window.onload = function() { setTimeout(function(){ window.print(); }, 500); }</script>'
                return content

        if os.path.exists('attack_map.html'):
             with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
             with open('attack_map.html', 'r', encoding='utf-8') as f:
                map_content = f.read()

             # Embed map
             map_html = f'''
            <div class="map-container" style="margin-top: 40px; border: 1px solid #30363D; border-radius: 8px; overflow: hidden; height: 900px; display: flex; flex-direction: column; page-break-before: always;">
                <div style="background: #161B22; padding: 12px 16px; border-bottom: 1px solid #30363D; font-family: 'Space Grotesk', sans-serif; font-size: 13px; color: #BC8CFF; font-weight: bold; display: flex; align-items: center; gap: 8px;">
                    <span>⚠️ INTERACTIVE ATTACK MAP</span>
                </div>
                <iframe srcdoc="{map_content.replace('"', '&quot;')}" style="width: 100%; height: 100%; border: none; flex: 1; background: #07090d;"></iframe>
            </div>
            '''
             content = content.replace('<div class="footer-note">', map_html + '<div class="footer-note">')
             
             # Add print script to auto-trigger print dialog
             content += '<script>window.onload = function() { setTimeout(function(){ window.print(); }, 500); }</script>'
             return content
        
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()

    except Exception as e:
        return f"Error viewing report: {str(e)}", 404

@app.route('/attack_map')
def attack_map():
    """Serve the generated attack map"""
    try:
        with open('attack_map.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Attack Map not generated yet. Generate a report first.</h1>", 404

@app.route('/save', methods=['POST'])
def save():
    import base64
    import json
    import os
    
    # Decode form data
    encoded_data = request.form['form_data']
    form_data = json.loads(base64.b64decode(encoded_data).decode('utf-8'))
    
    # Process form data (similar to /generate)
    data = {
        'title': form_data.get('title', 'Report'),
        'update_date': form_data.get('update_date', ''),
        'stats': {
            'subnets': form_data.get('subnets', ''),
            'hosts_found': form_data.get('hosts_found', ''),
            'ad_users': form_data.get('ad_users', ''),
            'credentials': form_data.get('credentials', ''),
            'root_shells': form_data.get('root_shells', ''),
            'dcs_found': form_data.get('dcs_found', ''),
            'smb_sign_off': form_data.get('smb_sign_off', '')
        },
        'compromised_hosts': [],
        'credentials': [],
        'users': [],
        'additional_data': [],
        'markdown': form_data.get('markdown', '')
    }
    
    # Process hosts
    host_ips = form_data.get('host_ip[]', [])
    if isinstance(host_ips, str): host_ips = [host_ips]
    host_services = form_data.get('host_service[]', [])
    if isinstance(host_services, str): host_services = [host_services]
    host_parents = form_data.get('host_parent[]', [])
    if isinstance(host_parents, str): host_parents = [host_parents]
    host_tags = form_data.get('host_tag[]', [])
    if isinstance(host_tags, str): host_tags = [host_tags]
    
    for i in range(len(host_ips)):
        service = host_services[i] if i < len(host_services) else ''
        if 'ROOT' in service.upper():
            service = service.replace('ROOT', '<b>ROOT</b>', 1)
        elif 'POSTGRES' in service.upper():
            service = service.replace('POSTGRES', '<b>POSTGRES</b>', 1)
        
        parent = host_parents[i] if i < len(host_parents) else ''
        
        data['compromised_hosts'].append({
            'ip': host_ips[i],
            'parent': parent,
            'service': service,
            'tag': host_tags[i] if i < len(host_tags) else ''
        })
    
    # Process credentials
    cred_sources = form_data.get('cred_source[]', [])
    if isinstance(cred_sources, str): cred_sources = [cred_sources]
    cred_credentials = form_data.get('cred_credential[]', [])
    if isinstance(cred_credentials, str): cred_credentials = [cred_credentials]
    cred_targets = form_data.get('cred_target[]', [])
    if isinstance(cred_targets, str): cred_targets = [cred_targets]
    cred_statuses = form_data.get('cred_status[]', [])
    if isinstance(cred_statuses, str): cred_statuses = [cred_statuses]
    
    for i in range(len(cred_sources)):
        credential = cred_credentials[i] if i < len(cred_credentials) else ''
        formatted_credential = f"<code>{credential}</code>"
        data['credentials'].append({
            'source': cred_sources[i],
            'credential': formatted_credential,
            'target': cred_targets[i] if i < len(cred_targets) else '',
            'status': cred_statuses[i] if i < len(cred_statuses) else ''
        })
    
    # Process uploaded files
    if 'users_file' in request.files:
        users_file = request.files['users_file']
        if users_file.filename:
            users_data = json.load(users_file)
            data['users'] = users_data.get('users', [])
    
    if 'additional_files' in request.files:
        additional_files = request.files.getlist('additional_files')
        for file in additional_files:
            if file.filename:
                add_data = json.load(file)
                data['additional_data'].append({
                    'filename': file.filename,
                    'data': add_data
                })
    
    # Generate HTML
    data['current_date'] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    data['num_hosts'] = len(data['compromised_hosts'])
    data['num_creds'] = len(data['credentials'])
    data['compromised_hosts_summary'] = ', '.join([host['ip'].split(' ')[0] for host in data['compromised_hosts']])
    
    data['compromised_hosts_html'] = generate_compromised_hosts_html(data['compromised_hosts'])
    data['credentials_html'] = generate_credentials_html(data['credentials'])
    data['users_html'] = generate_users_html(data['users'])
    data['additional_html'] = generate_additional_html(data['additional_data'])
    data['markdown_html'] = markdown_to_html(data['markdown'])
    
    html = REPORT_TEMPLATE_WITH_USERS.format(**data)
    
    # Save to file
    filename = request.form['filename']
    filepath = request.form['filepath']
    full_path = os.path.join(filepath, filename)
    os.makedirs(filepath, exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return f"Report saved to {full_path}"

def generate_users_html(users):
    if not users:
        return ""
    html = '<table class="users-table"><tr><th>ID</th><th>Username</th><th>Email</th><th>Full Name</th><th>Company</th><th>Role</th><th>Created At</th></tr>'
    for user in users:
        html += f"<tr><td>{user['id']}</td><td>{user['username']}</td><td>{user['email']}</td><td>{user['full_name']}</td><td>{user['company']}</td><td>{user['role']}</td><td>{user['created_at']}</td></tr>"
    html += '</table>'
    return html

def generate_additional_html(additional_data):
    html = ""
    for item in additional_data:
        html += f"<h3>{item['filename']}</h3>"
        if isinstance(item['data'], list):
            html += '<table class="data-table"><tr>'
            if item['data']:
                for key in item['data'][0].keys():
                    html += f"<th>{key}</th>"
                html += '</tr>'
                for row in item['data']:
                    html += '<tr>'
                    for value in row.values():
                        html += f"<td>{value}</td>"
                    html += '</tr>'
            html += '</table>'
        else:
            html += f"<pre>{json.dumps(item['data'], indent=2)}</pre>"
    return html

def markdown_to_html(markdown_text):
    if not markdown_text:
        return ""
    try:
        import markdown
        html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables', 'nl2br'])
        return f'<div class="markdown-content">{html}</div>'
    except ImportError:
        # Fallback: oddiy regex
        import re
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', markdown_text, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        html = re.sub(r'\n', r'<br>', html)
        return f'<div class="markdown-content">{html}</div>'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

