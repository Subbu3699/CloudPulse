
import { useEffect, useState } from "react";

import axios from "axios";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Pencil,
  Plus,
  RefreshCw,
  Server,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

function App() {
  const [apis, setApis] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [checks, setChecks] = useState([]);
  const [selectedApi, setSelectedApi] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [checkingId, setCheckingId] = useState(null);
  const [form, setForm] = useState({
    name: "",
    url: "",
    method: "GET",
    check_interval_seconds: 60,
    timeout_seconds: 10,
  });

  async function loadDashboard() {
    try {
      setError("");

      const [apiResponse, incidentResponse] = await Promise.all([
        API.get("/api/v1/monitored-apis"),
        API.get("/api/v1/incidents"),
      ]);

      setApis(apiResponse.data);
      setIncidents(incidentResponse.data);

      const results = await Promise.all(
        apiResponse.data.map(async (api) => {
          try {
            const response = await API.get(
              `/api/v1/monitored-apis/${api.id}/checks?limit=10`
            );
            return response.data.map((check) => ({
              ...check,
              api_name: api.name,
            }));
          } catch {
            return [];
          }
        })
      );

      setChecks(
        results
          .flat()
          .sort(
            (a, b) =>
              new Date(a.checked_at) - new Date(b.checked_at)
          )
      );
    } catch {
      setError(
        "Could not load dashboard data. Make sure the CloudPulse backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
    const timer = setInterval(loadDashboard, 30000);
    return () => clearInterval(timer);
  }, []);

  const latestByApi = apis.map((api) => {
    const latest = [...checks]
      .filter((check) => check.api_id === api.id)
      .sort(
        (a, b) =>
          new Date(b.checked_at) - new Date(a.checked_at)
      )[0];

    return {
      ...api,
      latest,
      healthy: latest ? latest.is_success : null,
    };
  });

  const healthyCount = latestByApi.filter(
    (api) => api.healthy === true
  ).length;

  const failingCount = latestByApi.filter(
    (api) => api.healthy === false
  ).length;

  const openIncidents = incidents.filter(
    (incident) => incident.status === "open"
  );


const visibleChecks = checks
  .filter(
    (check) =>
      selectedApi === "all" ||
      String(check.api_id) === selectedApi
  )
  .slice(-30);

const chartApis =
  selectedApi === "all"
    ? apis.filter((api) =>
        visibleChecks.some((check) => check.api_id === api.id)
      )
    : apis.filter((api) => String(api.id) === selectedApi);


  const chartData = visibleChecks.map((check) => {
    const point = { ...check };

    chartApis.forEach((api) => {
      point[`api_${api.id}`] =
        check.api_id === api.id
          ? check.response_time_ms
          : null;
    });

    return point;
  });



  function editApi(api) {
    setEditingId(api.id);
    setForm({
      name: api.name,
      url: api.url,
      method: api.method,
      check_interval_seconds: api.check_interval_seconds,
      timeout_seconds: api.timeout_seconds,
    });
    setShowForm(true);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function createApi(event) {
    event.preventDefault();

    const payload = {
      ...form,
      check_interval_seconds: Number(form.check_interval_seconds),
      timeout_seconds: Number(form.timeout_seconds),
    };

    try {
      setError("");

      if (editingId !== null) {
        await API.put(`/api/v1/monitored-apis/${editingId}`, payload);
      } else {
        await API.post("/api/v1/monitored-apis", payload);
      }

      setShowForm(false);
      setEditingId(null);
      setForm({
        name: "",
        url: "",
        method: "GET",
        check_interval_seconds: 60,
        timeout_seconds: 10,
      });

      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          (editingId !== null
            ? "Could not update the API."
            : "Could not create the API.")
      );
    }
  }

  async function runCheck(apiId) {
    setCheckingId(apiId);

    try {
      await API.post(
        `/api/v1/monitored-apis/${apiId}/check`
      );
      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.detail || "The API check failed to run."
      );
    } finally {
      setCheckingId(null);
    }
  }

  async function deleteApi(apiId, apiName) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${apiName}"?`
    );

    if (!confirmed) return;

    try {
      setError("");
      await API.delete(`/api/v1/monitored-apis/${apiId}`);
      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to delete the API."
      );
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview">
          <span className="brand-icon">
            <Activity size={23} />
          </span>
          <span>
            <strong>CloudPulse</strong>
            <small>API OBSERVABILITY</small>
          </span>
        </a>

        <p className="nav-label">WORKSPACE</p>
        <a className="nav-item active" href="#overview">
          <Activity size={18} /> Overview
        </a>
        <a className="nav-item" href="#monitored-apis">
          <Server size={18} /> Monitored APIs
        </a>
        <a className="nav-item" href="#incidents">
          <AlertTriangle size={18} /> Incidents
          {openIncidents.length > 0 && (
            <span className="nav-count">
              {openIncidents.length}
            </span>
          )}
        </a>
        <a className="nav-item" href="#history">
          <Clock size={18} /> Check history
        </a>

        <div className="sidebar-bottom">
          <span className="online-dot" />
          <span>Monitoring service</span>
          <strong>Online</strong>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">WORKSPACE / OVERVIEW</p>
            <h1>Monitoring dashboard</h1>
            <p className="muted">
              Monitor your endpoints and investigate incidents.
            </p>
          </div>

          <div className="topbar-actions">
            <button
              className="button secondary"
              onClick={loadDashboard}
              disabled={loading}
            >
              <RefreshCw size={16} /> Refresh
            </button>
            <button
              className="button primary"
              onClick={() => {
                if (showForm) {
                  setShowForm(false);
                  setEditingId(null);
                } else {
                  setEditingId(null);
                  setForm({
                    name: "",
                    url: "",
                    method: "GET",
                    check_interval_seconds: 60,
                    timeout_seconds: 10,
                  });
                  setError("");
                  setShowForm(true);
                }
              }}
            >
              <Plus size={17} /> Add API
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            <span>{error}</span>
            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}

        {showForm && (
          <section className="panel form-panel">
            <div className="panel-heading">
              <div>
                <h2>{editingId !== null ? "Edit monitored API" : "Add monitored API"}</h2>
                <p>
                  {editingId !== null
                    ? "Update this endpoint's monitoring settings."
                    : "Register an endpoint for monitoring."}
                </p>
              </div>
              <button
                className="icon-button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                }}
              >
                ✕
              </button>
            </div>

            <form className="api-form" onSubmit={createApi}>
              <label>
                API name
                <input
                  required
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  placeholder="Payments API"
                />
              </label>

              <label>
                Endpoint URL
                <input
                  required
                  type="url"
                  value={form.url}
                  onChange={(e) =>
                    setForm({ ...form, url: e.target.value })
                  }
                  placeholder="https://example.com/health"
                />
              </label>

              <label>
                HTTP method
                <select
                  value={form.method}
                  onChange={(e) =>
                    setForm({ ...form, method: e.target.value })
                  }
                >
                  <option>GET</option>
                  <option>HEAD</option>
                  <option>POST</option>
                  <option>PUT</option>
                  <option>DELETE</option>
                </select>
              </label>

              <label>
                Interval (seconds)
                <input
                  type="number"
                  min="10"
                  required
                  value={form.check_interval_seconds}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      check_interval_seconds: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Timeout (seconds)
                <input
                  type="number"
                  min="1"
                  required
                  value={form.timeout_seconds}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      timeout_seconds: e.target.value,
                    })
                  }
                />
              </label>

              <button className="button primary" type="submit">
                {editingId !== null ? "Save Changes" : "Create monitored API"}
              </button>
            </form>
          </section>
        )}

        <section className="welcome-row" id="overview">
          <div>
            <span className="live-badge">
              <span className="online-dot" /> LIVE MONITORING
            </span>
            <h2>Your APIs at a glance</h2>
            <p>
              Dashboard refreshes automatically every 30 seconds.
            </p>
          </div>
          <ShieldCheck size={48} className="welcome-icon" />
        </section>

        <section className="stats-grid">
          <StatCard
            title="Total APIs"
            value={apis.length}
            icon={<Server />}
            tone="blue"
            detail="Registered endpoints"
          />
          <StatCard
            title="Healthy APIs"
            value={healthyCount}
            icon={<CheckCircle2 />}
            tone="green"
            detail="Latest check succeeded"
          />
          <StatCard
            title="Failing APIs"
            value={failingCount}
            icon={<XCircle />}
            tone="red"
            detail="Latest check failed"
          />
          <StatCard
            title="Open incidents"
            value={openIncidents.length}
            icon={<AlertTriangle />}
            tone="orange"
            detail="Require investigation"
          />
        </section>

        <section className="content-grid">
          <div className="panel chart-panel" id="history">
            <div className="panel-heading">
              <div>
                <h2>Response time</h2>
                <p>Recent API check latency</p>
              </div>
              <select
                aria-label="Filter response-time chart by API"
                value={selectedApi}
                onChange={(e) => setSelectedApi(e.target.value)}
              >
                <option value="all">All APIs</option>
                {apis.map((api) => (
                  <option key={api.id} value={String(api.id)}>
                    {api.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="chart-container">
              {visibleChecks.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#e8edf4"
                    />
                    <XAxis
                      dataKey="checked_at"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      }
                      tick={{ fill: "#7c879a", fontSize: 11 }}
                      minTickGap={30}
                    />
                    <YAxis
                      tick={{ fill: "#7c879a", fontSize: 11 }}
                      tickCount={5}
                      domain={[0, "auto"]}
                      unit=" ms"
                      width={75}
                    />
                    <Tooltip
                      labelFormatter={(value) =>
                        new Date(value).toLocaleString()
                      }
                      formatter={(value, name) => [
                        `${Number(value).toFixed(2)} ms`,
                        name,
                      ]}
                    />
                    {chartApis.map((api, index) => (
                      <Line
                        key={api.id}
                        type="monotone"
                        dataKey={`api_${api.id}`}
                        name={api.name}
                        stroke={
                          [
                            "#4f6bed",
                            "#16a085",
                            "#e67e22",
                            "#9b59b6",
                            "#e74c3c",
                          ][index % 5]
                        }
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5 }}
                        connectNulls={true}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">
                  <Activity size={30} />
                  <strong>No check history yet</strong>
                  <span>Run a manual check to populate the chart.</span>
                </div>
              )}
            </div>
          </div>

          <div className="panel incidents-panel" id="incidents">
            <div className="panel-heading">
              <div>
                <h2>Open incidents</h2>
                <p>Detected monitoring failures</p>
              </div>
              <span className="count-badge">
                {openIncidents.length}
              </span>
            </div>

            {openIncidents.length ? (
              <div className="incident-list">
                {openIncidents.map((incident) => (
                  <div className="incident-item" key={incident.id}>
                    <span className="incident-icon">
                      <AlertTriangle size={18} />
                    </span>
                    <div className="incident-details">
                      <strong>{incident.title}</strong>
                      <span>
                        {incident.description || "No description"}
                      </span>
                      <small>
                        {new Date(
                          incident.started_at
                        ).toLocaleString()}
                      </small>
                    </div>
                    <span className="status-pill down">
                      {incident.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state compact">
                <CheckCircle2 size={28} />
                <strong>No open incidents</strong>
                <span>All monitored services look good.</span>
              </div>
            )}
          </div>
        </section>

        <section className="panel apis-panel" id="monitored-apis">
          <div className="panel-heading">
            <div>
              <h2>Monitored APIs</h2>
              <p>Endpoint health and manual controls</p>
            </div>
            <span className="table-total">
              {apis.length} endpoints
            </span>
          </div>

          {loading && apis.length === 0 ? (
            <p className="loading-text">Loading monitored APIs...</p>
          ) : apis.length === 0 ? (
            <div className="empty-state compact">
              <Server size={28} />
              <strong>No APIs registered</strong>
              <span>Click Add API to register your first endpoint.</span>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>API / ENDPOINT</th>
                    <th>METHOD</th>
                    <th>STATUS</th>
                    <th>LAST RESPONSE</th>
                    <th>INTERVAL</th>
                    <th>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {latestByApi.map((api) => (
                    <tr key={api.id}>
                      <td>
                        <div className="api-name">
                          <span className="api-avatar">
                            <Server size={17} />
                          </span>
                          <div>
                            <strong>{api.name}</strong>
                            <span className="endpoint-url">
                              {api.url}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="method-pill">
                          {api.method}
                        </span>
                      </td>
                      <td>
                        {api.healthy === true ? (
                          <span className="status-pill up">
                            <CheckCircle2 size={13} /> Healthy
                          </span>
                        ) : api.healthy === false ? (
                          <span className="status-pill down">
                            <XCircle size={13} /> Failing
                          </span>
                        ) : (
                          <span className="status-pill unknown">
                            Not checked
                          </span>
                        )}
                      </td>
                      <td>
                        {api.latest
                          ? `${api.latest.response_time_ms} ms`
                          : "—"}
                      </td>
                      <td>{api.check_interval_seconds}s</td>
                      <td>
                        <button
                          type="button"
                          className="button small secondary"
                          onClick={() => editApi(api)}
                        >
                          <Pencil size={14} /> Edit
                        </button>
                        <button
                          className="button small secondary"
                          disabled={checkingId === api.id}
                          onClick={() => runCheck(api.id)}
                        >
                          <RefreshCw size={14} />
                          {checkingId === api.id
                            ? "Checking..."
                            : "Check now"}
                        </button>
                        <button
                          type="button"
                          className="button small secondary"
                          onClick={() => deleteApi(api.id, api.name)}
                        >
                          <Trash2 size={14} /> Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <footer className="footer">
          <span>
            <Activity size={15} /> CloudPulse API Monitoring
          </span>
          <span>
            {loading ? "Connecting..." : "Dashboard connected"} ·
            Auto-refresh: 30 seconds
          </span>
        </footer>
      </main>
    </div>
  );
}

function StatCard({ title, value, icon, tone, detail }) {
  return (
    <article className="stat-card">
      <div className={`stat-icon ${tone}`}>{icon}</div>
      <p>{title}</p>
      <strong className="stat-value">{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

export default App;

