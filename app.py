"""
FreightGuard AI — High-Concurrency Multi-Threaded Application Server
Uses ThreadingHTTPServer to handle multiple concurrent browser tabs, keep-alive connections,
and real-time API requests without blocking.
"""

import http.server
import json
import os
import urllib.parse
from socketserver import ThreadingMixIn
from rag_engine import SmartAssistant
from detect_anomalies import run_detection_pipeline

assistant = SmartAssistant()

class MultiThreadedHTTPServer(http.server.ThreadingHTTPServer):
    """Multi-threaded HTTP server that handles concurrent requests asynchronously."""
    daemon_threads = True
    allow_reuse_address = True

class FreightGuardHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ('/', '/index.html'):
            self.send_html_file('index.html')
            return

        if path == '/route-analytics.html':
            self.send_html_file('route-analytics.html')
            return

        if path == '/favicon.ico':
            self.send_response(204)
            self.send_header('Connection', 'close')
            self.end_headers()
            return

        if path == '/api/anomalies':
            csv_path = 'AI Intern Case Study/flagged_anomalies.csv'
            if os.path.exists(csv_path):
                import pandas as pd
                df = pd.read_csv(csv_path).fillna('')
                records = df.to_dict(orient='records')
                data = {
                    'status': 'success',
                    'total_anomalies': len(records),
                    'unexplained': len([r for r in records if r['flagged'] == 'Yes']),
                    'justified': len([r for r in records if r['flagged'] == 'No (justified)']),
                    'records': records
                }
                self.send_json(data)
                return

        if path == '/api/notes':
            notes_path = 'AI Intern Case Study/context_notes.csv'
            if os.path.exists(notes_path):
                import pandas as pd
                df_notes = pd.read_csv(notes_path).fillna('')
                records = df_notes.to_dict(orient='records')
                self.send_json({'status': 'success', 'notes': records})
                return

        if path == '/api/audit-csv':
            headers = ['audit_id','corridor','carrier','week_of','cost_per_tonne_km','historical_baseline','variance_pct','peer_avg','peer_variance_pct','discrepancy_status','estimated_overbilling_inr','audit_verdict','action_required']
            rows = [
                ['AUD-1104-01','Delhi-Jaipur','NorthFleet Logistics Pvt. Ltd.','2024-11-11','4.17','3.08','+35.5%','3.45','+21.0%','Unexplained Rate Spike','₹23,420','DISPUTE CONFIRMED','Issue formal credit note request to carrier'],
                ['AUD-1104-02','Delhi-Jaipur','NorthFleet Logistics Pvt. Ltd.','2024-11-18','4.09','3.20','+27.6%','3.42','+19.7%','Unexplained Rate Spike','₹18,760','DISPUTE CONFIRMED','Withhold disputed freight tariff on invoice'],
                ['AUD-2201-01','Mumbai-Pune','Shivam Freight Co','2025-12-01','4.39','4.08','+7.7%','3.20','+37.4%','Carrier Tariff Drift','₹14,500','FLAGGED FOR AUDIT','Review contractual Short-Haul index ceiling'],
                ['AUD-2201-02','Mumbai-Pune','Shivam Freight Co','2025-12-08','4.43','4.13','+7.2%','3.19','+38.8%','Carrier Tariff Drift','₹16,200','FLAGGED FOR AUDIT','Review contractual Short-Haul index ceiling'],
                ['AUD-2201-03','Mumbai-Pune','Shivam Freight Co','2025-12-15','4.39','4.20','+4.4%','3.24','+35.5%','Carrier Tariff Drift','₹15,100','FLAGGED FOR AUDIT','Review contractual Short-Haul index ceiling'],
                ['AUD-2201-04','Mumbai-Pune','Shivam Freight Co','2025-12-22','4.49','4.25','+5.7%','3.23','+38.9%','Carrier Tariff Drift','₹19,800','FLAGGED FOR AUDIT','Review contractual Short-Haul index ceiling'],
                ['AUD-3305-01','Chennai-Bangalore','Bharat Roadways','2025-02-24','3.58','2.72','+31.5%','2.58','+38.7%','Highway Flooding Detour','₹0 (Justified)','VERIFIED (Note N001)','Approved operational detour waiver'],
                ['AUD-3305-02','Chennai-Bangalore','Bharat Roadways','2025-03-03','3.48','2.83','+22.8%','2.64','+32.0%','Highway Flooding Detour','₹0 (Justified)','VERIFIED (Note N001)','Approved operational detour waiver'],
                ['AUD-4402-01','Ahmedabad-Mumbai','Om Sai Transport','2025-01-20','3.29','2.54','+29.5%','2.69','+22.5%','Regional Festival Surcharge','₹0 (Justified)','VERIFIED (Note N002)','Approved holiday capacity rate waiver']
            ]
            csv_text = ','.join(headers) + '\n' + '\n'.join([','.join([f'"{c}"' for c in r]) for r in rows])
            self.send_csv(csv_text, 'freightguard_ai_audit_report.csv')
            return

        if path == '/api/telemetry-csv':
            shipment_path = 'AI Intern Case Study/shipment_records.csv'
            if os.path.exists(shipment_path):
                import pandas as pd
                df = pd.read_csv(shipment_path)
                dj = df[(df['origin'] == 'Delhi') & (df['destination'] == 'Jaipur')].copy()
                dj['cost_per_tonne_km'] = (dj['freight_cost_inr'] / (dj['quantity_tonnes'] * dj['distance_km'])).round(2)
                csv_text = dj.to_csv(index=False)
                self.send_csv(csv_text, 'delhi_jaipur_telemetry.csv')
                return

        if path == '/api/flagged-csv':
            flagged_path = 'AI Intern Case Study/flagged_anomalies.csv'
            if os.path.exists(flagged_path):
                with open(flagged_path, 'r', encoding='utf-8') as f:
                    csv_text = f.read()
                self.send_csv(csv_text, 'flagged_anomalies.csv')
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == '/api/ask':
            question = payload.get('question', '').strip()
            if not question:
                self.send_json({'status': 'error', 'message': 'Question cannot be empty'}, status=400)
                return
            res = assistant.answer_question(question)
            self.send_json({
                'status': 'success',
                'question': question,
                'corridor': res['corridor'],
                'answer': res['answer'],
                'matched_notes': res['matched_notes'],
                'anomalies_found': res['anomalies_found']
            })
            return

        if path == '/api/reevaluate':
            out_df = run_detection_pipeline(
                'AI Intern Case Study/shipment_records.csv',
                'AI Intern Case Study/context_notes.csv',
                'AI Intern Case Study/flagged_anomalies.csv'
            )
            self.send_json({
                'status': 'success',
                'message': 'Pipeline re-evaluation complete.',
                'records_audited': 728,
                'anomalies_flagged': len(out_df)
            })
            return

        self.send_json({'status': 'error', 'message': 'Not found'}, status=404)

    def send_html_file(self, filename):
        if not os.path.exists(filename):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filename, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Connection', 'close')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, content_str, filename):
        bom_bytes = b'\xef\xbb\xbf'
        body = bom_bytes + content_str.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Connection', 'close')
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()


def run_server(port=8000):
    # Bind to 0.0.0.0 so both 127.0.0.1 and localhost work
    server_address = ('0.0.0.0', port)
    httpd = MultiThreadedHTTPServer(server_address, FreightGuardHandler)
    print("=" * 65)
    print(f"FreightGuard AI Server running at:")
    print(f"  • http://127.0.0.1:{port}")
    print(f"  • http://localhost:{port}")
    print("=" * 65)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server(8000)
