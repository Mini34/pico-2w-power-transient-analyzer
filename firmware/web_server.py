import socket

try:
    import ujson as json
except ImportError:
    import json


DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pico 2 W EE Lab Tool</title>
<style>
:root{--ink:#16251f;--muted:#607069;--paper:#f4f0e5;--card:#fffdf6;--line:#d8d1bf;--teal:#147d72;--orange:#d9662b;--yellow:#e4ad37}
*{box-sizing:border-box}body{margin:0;color:var(--ink);font-family:Georgia,"Times New Roman",serif;background:radial-gradient(circle at 10% 0,#fff8d6 0,transparent 35%),linear-gradient(135deg,#e7efe8,var(--paper) 60%);min-height:100vh}
main{width:min(1180px,calc(100% - 28px));margin:auto;padding:28px 0 48px}.mast{display:flex;gap:20px;justify-content:space-between;align-items:end;border-bottom:3px solid var(--ink);padding-bottom:18px}.eyebrow,.label,.stamp,.chart-note,th,td{font-family:"Courier New",monospace}.eyebrow{font-weight:700;font-size:12px;letter-spacing:.15em;color:var(--orange)}h1{font-size:clamp(34px,6vw,72px);line-height:.92;margin:7px 0 0}.subtitle{font:700 13px/1.5 "Courier New",monospace;color:var(--muted)}h2{font-size:18px;margin:0 0 14px;border-bottom:1px solid var(--line);padding-bottom:9px}
.status,.system-grid,.fault-grid,.cards{display:grid;gap:1px;background:var(--line);border:1px solid var(--line)}.status,.system-grid{grid-template-columns:repeat(4,1fr)}.fault-grid{grid-template-columns:repeat(5,1fr)}.status{margin:18px 0}.status div,.system-grid div,.fault-grid div,.card,.panel{background:rgba(255,253,246,.93)}.status div,.system-grid div,.fault-grid div{padding:12px}.label{font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}.status strong,.system-grid strong,.fault-grid strong{display:block;margin-top:5px}.online{color:var(--teal)}.offline{color:var(--orange)}.system-panel,.fault-panel{margin:18px 0}
.cards{grid-template-columns:repeat(3,1fr);gap:12px;background:none;border:0}.card{border:1px solid var(--line);padding:18px;min-height:118px;box-shadow:4px 4px 0 rgba(22,37,31,.08)}.value{font:700 clamp(27px,4vw,46px)/1 "Courier New",monospace;margin-top:18px}.unit{font-size:.42em;color:var(--muted)}.grid{display:grid;grid-template-columns:1.25fr .75fr;gap:16px;margin-top:16px}.panel{border:1px solid var(--line);padding:16px}.metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.metric{border-bottom:1px dashed var(--line);padding:8px 0}.metric b{display:block;font:700 17px/1.4 "Courier New",monospace;margin-top:3px}
.charts{display:grid;gap:12px;margin-top:16px}canvas{width:100%;height:150px;background:#fbf8ef;border:1px solid var(--line)}.chart-note{margin:-7px 0 12px;color:var(--muted);font-size:12px}.downloads{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.downloads a{color:var(--ink);background:var(--yellow);border:1px solid var(--ink);padding:8px 11px;text-decoration:none;font:700 12px "Courier New",monospace}.table-wrap{overflow:auto;border:1px solid var(--line);background:var(--card)}table{width:100%;border-collapse:collapse;min-width:720px}th,td{text-align:left;padding:9px;border-bottom:1px solid var(--line);font-size:12px}th{color:var(--muted)}.stamp{font-size:12px;color:var(--muted);margin-top:18px}
@media(max-width:760px){.mast{display:block}.subtitle{margin-top:16px}.status,.system-grid,.fault-grid,.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}@media(max-width:460px){.status,.system-grid,.fault-grid,.cards,.metrics{grid-template-columns:1fr}h1{font-size:38px}}
</style></head><body><main>
<header class="mast"><div><div class="eyebrow">PICO 2 W / LOCAL INSTRUMENT</div><h1>EE Lab Tool</h1></div><div class="subtitle">Embedded Electrical Characterization Platform<br>Read-only local dashboard</div></header>
<section class="status"><div><span class="label">Device</span><strong id="device">Connecting</strong></div><div><span class="label">Wi-Fi</span><strong id="wifi">Checking</strong></div><div><span class="label">IP</span><strong id="ip">--</strong></div><div><span class="label">Mode / Uptime</span><strong id="mode">--</strong></div></section>
<section class="system-panel"><h2>System</h2><div class="system-grid"><div><span class="label">MCU Temperature</span><strong id="system-temp">--</strong></div><div><span class="label">Wi-Fi</span><strong id="system-wifi">--</strong></div><div><span class="label">Mode</span><strong id="system-mode">--</strong></div><div><span class="label">Logging</span><strong id="logging">--</strong></div></div></section>
<section class="fault-panel"><h2>System Status / Threshold Monitoring</h2><div class="fault-grid"><div><span class="label">INA219</span><strong id="fault-ina">--</strong></div><div><span class="label">Voltage</span><strong id="fault-voltage">--</strong></div><div><span class="label">Current</span><strong id="fault-current">--</strong></div><div><span class="label">Power</span><strong id="fault-power">--</strong></div><div><span class="label">MCU Temp</span><strong id="fault-temp">--</strong></div></div><p class="chart-note">Software monitoring only. No automatic electrical cutoff is provided.</p></section>
<section><h2>Live Power</h2><div class="cards"><article class="card"><span class="label">Voltage</span><div class="value"><span id="voltage">--</span> <span class="unit">V</span></div></article><article class="card"><span class="label">Current</span><div class="value"><span id="current">--</span> <span class="unit">A</span></div></article><article class="card"><span class="label">Power</span><div class="value"><span id="power">--</span> <span class="unit">W</span></div></article></div></section>
<div class="grid"><section class="panel"><h2>Power Monitor</h2><div class="metrics"><div class="metric"><span class="label">Charge</span><b id="charge">--</b></div><div class="metric"><span class="label">Energy</span><b id="energy">--</b></div><div class="metric"><span class="label">Elapsed</span><b id="elapsed">--</b></div><div class="metric"><span class="label">Minimum voltage</span><b id="minv">--</b></div><div class="metric"><span class="label">Maximum voltage</span><b id="maxv">--</b></div><div class="metric"><span class="label">Peak current</span><b id="peaki">--</b></div><div class="metric"><span class="label">Peak power</span><b id="peakp">--</b></div><div class="metric"><span class="label">Average voltage</span><b id="avgv">--</b></div><div class="metric"><span class="label">Average current</span><b id="avgi">--</b></div><div class="metric"><span class="label">Average power</span><b id="avgp">--</b></div></div></section>
<div><section class="panel"><h2>RC Analyzer</h2><div class="metric"><span class="label">Tau</span><b id="tau">--</b></div><div class="metric"><span class="label">Capacitance</span><b id="cap">--</b></div><div class="metric"><span class="label">Last run</span><b id="rclast">--</b></div></section><section class="panel" style="margin-top:16px"><h2>Diode Analyzer</h2><div class="metric"><span class="label">Classification</span><b id="dclass">--</b></div><div class="metric"><span class="label">Forward voltage</span><b id="vf">--</b></div><div class="metric"><span class="label">Test current / source</span><b id="diodeextra">--</b></div><div class="metric"><span class="label">Last run</span><b id="dlast">--</b></div></section><section class="panel" style="margin-top:16px"><h2>Source Test</h2><div class="metric"><span class="label">Voc</span><b id="voc">--</b></div><div class="metric"><span class="label">Source resistance</span><b id="rs">--</b></div><div class="metric"><span class="label">Fit / points</span><b id="sourcefit">--</b></div></section></div></div>
<section class="charts"><h2>Recent Power History</h2><canvas id="vchart"></canvas><canvas id="ichart"></canvas><canvas id="pchart"></canvas></section>
<section class="charts"><h2>RC Analyzer Traces</h2><p class="chart-note">Last completed RC run. Charge and discharge voltage are plotted against elapsed measurement time.</p><canvas id="rcchargechart"></canvas><canvas id="rcdischargechart"></canvas></section>
<section class="charts"><h2>MCU Temperature</h2><p class="chart-note">Internal Pico die telemetry, not ambient temperature. Up to 30 minutes.</p><canvas id="tempchart"></canvas></section>
<section class="panel" style="margin-top:18px"><h2>Experiment History / Logs</h2><div class="downloads"><a href="/export/experiments.csv">Download Experiment CSV</a><a href="/export/experiments.json">Download Experiment JSON</a><a href="/export/faults.csv">Download Fault CSV</a><a href="/export/faults.json">Download Fault JSON</a></div><div class="table-wrap"><table><thead><tr><th>Uptime</th><th>Type</th><th>Status</th><th>Summary</th></tr></thead><tbody id="logrows"><tr><td colspan="4">Waiting for records...</td></tr></tbody></table></div></section>
<div class="stamp" id="stamp">Waiting for device data...</div>
</main><script>
const $=id=>document.getElementById(id);const f=(v,n=3)=>v==null?'--':Number(v).toFixed(n);const age=(ms,up)=>ms==null?'--':Math.max(0,Math.round(up-ms/1000))+' s ago';let stateBusy=false,stateFailures=0,historyBusy=false,rcBusy=false,tempBusy=false,logsBusy=false,maxVoltage=null,lastPowerElapsed=null;
function setText(id,text){$(id).textContent=text}function clock(seconds){seconds=Math.max(0,Math.round(seconds||0));const h=String(Math.floor(seconds/3600)).padStart(2,'0'),m=String(Math.floor((seconds%3600)/60)).padStart(2,'0'),s=String(seconds%60).padStart(2,'0');return h+':'+m+':'+s}
function faultLabel(states,key,alert){const item=states[key]||{};return item.active?alert:'OK'}
async function state(){if(stateBusy)return;stateBusy=true;try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error(r.status);const s=await r.json(),w=s.wifi||{},sys=s.system||{},p=s.power||{},rc=s.rc||{},d=s.diode||{},lg=s.logging||{},src=s.source_test||{},fault=s.faults||{},states=fault.states||{};stateFailures=0;setText('device','Online');$('device').className='online';setText('wifi',w.connected?'Connected':(w.status||'Offline'));$('wifi').className=w.connected?'online':'offline';setText('ip',w.ip||'--');setText('mode',(s.mode||'--')+' / '+Math.round(s.uptime_s||0)+' s');setText('system-temp',sys.temperature_c==null?'--':f(sys.temperature_c,1)+' \u00b0C');setText('system-wifi',w.connected?'Connected':'Disconnected');setText('system-mode',s.mode||'--');setText('logging',lg.available?'Ready':(lg.last_error?'Error':'Unavailable'));setText('fault-ina',faultLabel(states,'INA219_LOST','OFFLINE'));setText('fault-voltage',faultLabel(states,'UNDERVOLTAGE','LOW'));setText('fault-current',faultLabel(states,'OVERCURRENT','HIGH'));setText('fault-power',faultLabel(states,'OVERPOWER','HIGH'));setText('fault-temp',faultLabel(states,'MCU_TEMP_HIGH','HIGH'));setText('voltage',f(p.voltage_v));setText('current',f(p.current_a));setText('power',f(p.power_w));setText('charge',f(p.charge_mAh,2)+' mAh');setText('energy',f(p.energy_Wh,4)+' Wh');setText('elapsed',p.elapsed_s==null?'--':Math.round(p.elapsed_s)+' s');setText('minv',f(p.min_voltage_v)+' V');if(p.elapsed_s!=null&&(lastPowerElapsed==null||p.elapsed_s<lastPowerElapsed))maxVoltage=null;lastPowerElapsed=p.elapsed_s;if(p.voltage_v!=null){const liveV=Number(p.voltage_v);if(Number.isFinite(liveV))maxVoltage=maxVoltage==null?liveV:Math.max(maxVoltage,liveV)}setText('maxv',f(maxVoltage)+' V');setText('peaki',f(p.peak_current_a)+' A');setText('peakp',f(p.peak_power_w)+' W');setText('avgv',f(p.avg_voltage_v)+' V');setText('avgi',f(p.avg_current_a)+' A');setText('avgp',f(p.avg_power_w)+' W');setText('tau',f(rc.tau_s,3)+' s');setText('cap',f(rc.capacitance_uF,0)+' uF');setText('rclast',age(rc.last_run_ms,s.uptime_s));setText('dclass',d.classification||'--');setText('vf',f(d.forward_voltage_v)+' V');setText('diodeextra',f(d.current_mA,2)+' mA / '+f(d.test_voltage_v)+' V');setText('dlast',age(d.last_run_ms,s.uptime_s));setText('voc',f(src.voc_v)+' V');setText('rs',f(src.source_resistance_ohm)+' ohm');setText('sourcefit',(src.r_squared==null?'--':f(src.r_squared,3))+' / '+(src.point_count||0)+' pts');setText('stamp','Updated '+new Date().toLocaleTimeString())}catch(e){stateFailures++;if(stateFailures>=3){setText('device','Unavailable');$('device').className='offline';setText('stamp','Dashboard connection lost')}else setText('stamp','Update delayed ('+stateFailures+'/3)')}finally{stateBusy=false}}
function graph(id,data,key,label,color,xKey='t',xLabel='Time (s)'){const c=$(id),dpr=devicePixelRatio||1,w=c.clientWidth,h=c.clientHeight;c.width=Math.max(1,w*dpr);c.height=Math.max(1,h*dpr);const ctx=c.getContext('2d'),left=54,right=14,top=26,bottom=38,plotW=Math.max(1,w-left-right),plotH=Math.max(1,h-top-bottom),axis=n=>Math.abs(n)>=100?n.toFixed(0):n.toFixed(2);ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);ctx.font='12px Courier New';ctx.fillStyle='#607069';ctx.textAlign='left';ctx.fillText(label,10,16);ctx.textAlign='center';ctx.fillText(xLabel,left+plotW/2,h-6);ctx.textAlign='left';if(!data.length){ctx.fillText('No completed data',left+8,top+18);return}const points=data.map(q=>({x:Number(q[xKey]),y:Number(q[key])})).filter(q=>Number.isFinite(q.x)&&Number.isFinite(q.y));if(!points.length){ctx.fillText('No valid data',left+8,top+18);return}let xlo=Math.min(...points.map(q=>q.x)),xhi=Math.max(...points.map(q=>q.x)),ylo=Math.min(...points.map(q=>q.y)),yhi=Math.max(...points.map(q=>q.y));if(xhi===xlo){xhi+=.5;xlo-=.5}if(yhi===ylo){const pad=Math.abs(yhi)*.05||1;yhi+=pad;ylo-=pad}ctx.strokeStyle='#d8d1bf';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(left,top);ctx.lineTo(left,top+plotH);ctx.lineTo(left+plotW,top+plotH);ctx.stroke();ctx.fillStyle='#607069';ctx.textAlign='right';ctx.fillText(axis(yhi),left-6,top+4);ctx.fillText(axis(ylo),left-6,top+plotH+4);ctx.textAlign='left';ctx.fillText(axis(xlo),left,top+plotH+16);ctx.textAlign='right';ctx.fillText(axis(xhi),left+plotW,top+plotH+16);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();points.forEach((point,i)=>{const px=left+(point.x-xlo)*plotW/(xhi-xlo),py=top+(yhi-point.y)*plotH/(yhi-ylo);i?ctx.lineTo(px,py):ctx.moveTo(px,py)});ctx.stroke();if(points.length===1){const point=points[0],px=left+(point.x-xlo)*plotW/(xhi-xlo),py=top+(yhi-point.y)*plotH/(yhi-ylo);ctx.beginPath();ctx.arc(px,py,4,0,Math.PI*2);ctx.fillStyle=color;ctx.fill()}}
async function history(){if(historyBusy)return;historyBusy=true;try{const r=await fetch('/api/power-history',{cache:'no-store'}),d=await r.json();const hv=d.map(q=>Number(q.v)).filter(Number.isFinite);if(hv.length){const hm=Math.max(...hv);maxVoltage=maxVoltage==null?hm:Math.max(maxVoltage,hm);setText('maxv',f(maxVoltage)+' V')}graph('vchart',d,'v','Voltage (V)','#147d72','t','Time since boot (s)');graph('ichart',d,'i','Current (A)','#d9662b','t','Time since boot (s)');graph('pchart',d,'p','Power (W)','#9b7415','t','Time since boot (s)')}catch(e){}finally{historyBusy=false}}
async function rcHistory(){if(rcBusy)return;rcBusy=true;try{const r=await fetch('/api/rc-history',{cache:'no-store'}),d=await r.json();graph('rcchargechart',d.charge||[],'v','Charge Voltage (V)','#147d72','t','Elapsed time (s)');graph('rcdischargechart',d.discharge||[],'v','Discharge Voltage (V)','#d9662b','t','Elapsed time (s)')}catch(e){}finally{rcBusy=false}}
async function tempHistory(){if(tempBusy)return;tempBusy=true;try{const r=await fetch('/api/temperature-history',{cache:'no-store'}),d=await r.json();graph('tempchart',d,'temp_c','MCU Temperature (C)','#0b7a75','t','Time since boot (s)')}catch(e){}finally{tempBusy=false}}
function summary(record){const d=record.data||{},t=record.type||'';if(t==='POWER')return f(d.elapsed_s,1)+' s, '+f(d.energy_Wh,4)+' Wh';if(t==='RC')return 'tau '+f(d.tau_s,3)+' s, '+f(d.capacitance_uF,0)+' uF';if(t==='DIODE_SINGLE')return (d.classification||'--')+', Vf '+f(d.forward_voltage_v,3)+' V';if(t==='DIODE_IV')return (d.point_count||0)+' points, Imax '+f(d.max_current_mA,2)+' mA';if(t==='SOURCE TEST')return 'Voc '+f(d.voc_v,3)+' V, Rs '+f(d.source_resistance_ohm,3)+' ohm';if(t==='FAULT')return (d.fault_code||'FAULT')+' '+(d.fault_state||'');return t}
function renderLogs(rows){const body=$('logrows');body.textContent='';if(!rows.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=4;td.textContent='No completed experiments or fault events yet.';tr.appendChild(td);body.appendChild(tr);return}[...rows].reverse().forEach(record=>{const tr=document.createElement('tr');[clock(record.uptime_s),record.type||'--',record.status||'--',summary(record)].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.appendChild(td)});body.appendChild(tr)})}
async function logs(){if(logsBusy)return;logsBusy=true;try{const r=await fetch('/api/logs',{cache:'no-store'}),d=await r.json();renderLogs(d)}catch(e){}finally{logsBusy=false}}
async function stateLoop(){await state();setTimeout(stateLoop,2000)}async function historyLoop(){await history();setTimeout(historyLoop,5000)}async function rcLoop(){await rcHistory();setTimeout(rcLoop,5000)}async function tempLoop(){await tempHistory();setTimeout(tempLoop,10000)}async function logLoop(){await logs();setTimeout(logLoop,20000)}stateLoop();historyLoop();setTimeout(rcLoop,750);setTimeout(tempLoop,1000);setTimeout(logLoop,2000);addEventListener('resize',()=>{history();rcHistory();tempHistory()});
</script></body></html>"""

DASHBOARD_HTML = DASHBOARD_HTML.replace(
    "<h2>Source Test</h2>",
    "<h2>Source Test</h2><div class=\"metric\"><span class=\"label\">Status</span><b id=\"sourcestatus\">--</b></div>",
)
DASHBOARD_HTML = DASHBOARD_HTML.replace(
    "setText('voc',f(src.voc_v)+' V');",
    "setText('sourcestatus',(src.status||'idle').toUpperCase());$('sourcestatus').className=src.status==='invalid'?'offline':'';setText('voc',f(src.voc_v)+' V');",
)
DASHBOARD_HTML = DASHBOARD_HTML.replace(
    "setText('sourcefit',(src.r_squared==null?'--':f(src.r_squared,3))+' / '+(src.point_count||0)+' pts');",
    "setText('sourcefit',src.status==='invalid'?'INVALID: '+(src.reason||src.warning||'fit rejected'):(src.r_squared==null?'--':f(src.r_squared,3))+' / '+(src.point_count||0)+' pts');",
)

_DASHBOARD_BYTES = DASHBOARD_HTML.encode("utf-8")


class WebServer:
    def __init__(self, state_module, logger=None, port=80):
        self.state = state_module
        self.logger = logger
        self.port = port
        self.server = None

    def start(self):
        if self.server is not None:
            return True
        try:
            address = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
            server = socket.socket()
            try:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception:
                pass
            server.bind(address)
            server.listen(1)
            server.setblocking(False)
            self.server = server
            print("WEB  | listening | :{}".format(self.port))
            return True
        except Exception as exc:
            self.server = None
            print("WEB  | start error |", exc)
            return False

    def stop(self):
        if self.server is not None:
            try:
                self.server.close()
            except Exception:
                pass
        self.server = None

    def _send_all(self, client, data):
        sent = 0
        while sent < len(data):
            count = client.send(data[sent:])
            if not count:
                break
            sent += count

    def _respond(self, client, status, content_type, body, filename=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        header = (
            "HTTP/1.1 {}\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
        ).format(status, content_type, len(body))
        if filename:
            header += 'Content-Disposition: attachment; filename="{}"\r\n'.format(filename)
        header += "Connection: close\r\n\r\n"
        self._send_all(client, header.encode("utf-8"))
        self._send_all(client, body)

    def _logger_json(self, kind):
        if self.logger is None:
            return "[]"
        return self.logger.export_json(kind)

    def _logger_csv(self, kind):
        if self.logger is None:
            return ""
        return self.logger.export_csv(kind)

    def _handle(self, client):
        client.settimeout(0.75)
        request = client.recv(1024)
        if not request:
            return
        try:
            first_line = request.decode("utf-8").split("\r\n", 1)[0]
            method, path, _ = first_line.split(" ", 2)
            path = path.split("?", 1)[0]
        except Exception:
            self._respond(client, "400 Bad Request", "text/plain", "Bad request")
            return
        print("WEB  | {} {}".format(method, path))
        if method != "GET":
            self._respond(client, "405 Method Not Allowed", "text/plain", "Read-only dashboard")
        elif path == "/":
            self._respond(client, "200 OK", "text/html; charset=utf-8", _DASHBOARD_BYTES)
        elif path == "/api/state":
            self._respond(client, "200 OK", "application/json", json.dumps(self.state.snapshot()))
        elif path == "/api/power-history":
            self._respond(client, "200 OK", "application/json", json.dumps(self.state.power_history()))
        elif path == "/api/temperature-history":
            self._respond(client, "200 OK", "application/json", json.dumps(self.state.temperature_history()))
        elif path == "/api/rc-history":
            self._respond(client, "200 OK", "application/json", json.dumps(self.state.rc_history()))
        elif path in ("/api/logs", "/api/logs.json"):
            records = [] if self.logger is None else self.logger.recent_combined(30)
            self._respond(client, "200 OK", "application/json", json.dumps(records))
        elif path == "/api/faults":
            records = [] if self.logger is None else self.logger.recent("faults", 30)
            self._respond(client, "200 OK", "application/json", json.dumps(records))
        elif path == "/export/experiments.json":
            self._respond(client, "200 OK", "application/json", self._logger_json("experiments"), "experiments.json")
        elif path == "/export/faults.json":
            self._respond(client, "200 OK", "application/json", self._logger_json("faults"), "faults.json")
        elif path == "/export/experiments.csv":
            self._respond(client, "200 OK", "text/csv; charset=utf-8", self._logger_csv("experiments"), "experiments.csv")
        elif path == "/export/faults.csv":
            self._respond(client, "200 OK", "text/csv; charset=utf-8", self._logger_csv("faults"), "faults.csv")
        else:
            self._respond(client, "404 Not Found", "text/plain", "Not found")

    def poll(self):
        if self.server is None:
            return
        try:
            client, _ = self.server.accept()
        except OSError:
            return
        try:
            self._handle(client)
        except Exception as exc:
            print("WEB  | request error |", exc)
        finally:
            try:
                client.close()
            except Exception:
                pass
