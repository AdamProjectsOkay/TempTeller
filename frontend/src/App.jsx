import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import Gauge from "./Gauge.jsx";

// Scale the whole (fixed-width) page up or down so it always fits the window
// while keeping its exact proportions. Caps growth so it never gets huge.
function useFitToWindow(ready) {
  const ref = useRef(null);
  const fit = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.zoom = "1";
    const z = Math.min(window.innerWidth / el.scrollWidth,
                       window.innerHeight / el.scrollHeight, 1.6);
    el.style.zoom = String(Math.max(0.3, z));
  }, []);

  useLayoutEffect(() => {
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [fit]);

  // Re-fit once the first data arrives (content height changes).
  useEffect(() => { if (ready) fit(); }, [ready, fit]);

  return ref;
}

function useMetrics() {
  const [data, setData] = useState(null);
  const [procs, setProcs] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let stopped = false;
    let retry;

    function connect() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${proto}://${location.host}/ws`);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        const d = JSON.parse(e.data);
        setData(d);
        // Process list only arrives every 5s; keep the last one otherwise.
        if (d.processes) setProcs(d.processes);
      };
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) retry = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws.close();
    }
    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  return { data, procs, connected };
}

export default function App() {
  const { data, procs, connected } = useMetrics();
  const pageRef = useFitToWindow(!!data);

  return (
    <div className="viewport">
    <div className="page" ref={pageRef}>
      <header>
        <h1>TempTeller</h1>
        <span className={`status ${connected ? "on" : "off"}`}>
          {connected ? "live" : "reconnecting…"}
        </span>
      </header>

      {!data ? (
        <div className="loading">Waiting for first reading…</div>
      ) : (
        <>
          <section className="grid">
            {data.dials.map((d) => (
              <Gauge key={d.label} label={d.label} temp={d.temp}
                     tempMax={d.tempMax} usage={d.usage} />
            ))}
          </section>
          <p className="legend">
            <span className="swatch outer" /> outer ring: temperature
            <span className="swatch inner" /> inner ring: usage
          </p>

          <section className="details">
            <div className="card stats">
              <div className="stat">
                <span className="k">CPU</span>
                <span className="v">{data.cpu.percent.toFixed(0)}% · {data.cpu.freq} GHz · {data.cpu.cores} cores</span>
              </div>
              <div className="stat">
                <span className="k">RAM</span>
                <span className="v">{data.ram.used_gb} / {data.ram.total_gb} GB</span>
              </div>
            </div>

            <div className="card">
              <h2>Top Processes</h2>
              <table>
                <thead>
                  <tr><th>Process</th><th>PID</th><th>CPU%</th><th>Mem%</th><th>Mem (MB)</th></tr>
                </thead>
                <tbody>
                  {procs.map((p) => (
                    <tr key={p.pid}>
                      <td className="pname">{p.name}</td>
                      <td>{p.pid}</td>
                      <td>{p.cpu}</td>
                      <td>{p.mem}</td>
                      <td>{p.mem_mb}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
    </div>
  );
}
