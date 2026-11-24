import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./App.css";
import StaffDashboard from "./StaffDashboard";

/* ------------------------------------------------------------------
   API SETTINGS Ã¢â‚¬â€ the only block you may need to adjust.
   If your original App.jsx used different URLs or field names,
   copy them here. Nothing else in this file talks to the backend.
------------------------------------------------------------------- */
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ENDPOINTS = {
  services: "/services/",
  createToken: "/tokens/",
  // Status is looked up by the token number (e.g. "ACC-003"), NOT the database ID.
  tokenStatus: (tokenNumber) => `/tokens/${encodeURIComponent(tokenNumber)}`,
};

// Request body for generating a token.
const buildTokenRequest = (serviceId) => ({ service_id: Number(serviceId) });

// Pick values out of API responses (first matching field wins).
const pick = (obj, keys) => {
  for (const k of keys) {
    if (obj && obj[k] !== undefined && obj[k] !== null) return obj[k];
  }
  return null;
};
// Deliberately no "id" fallback: the backend identifies tokens by token number.
const getTokenNumber = (t) => pick(t, ["token_number", "number", "token"]);
const getStatus = (t) => pick(t, ["status", "state"]);
const getAhead = (t) => pick(t, ["people_ahead", "ahead", "position_ahead", "queue_position"]);
const getWait = (t) =>
  pick(t, ["estimated_wait_time", "estimated_waiting_time", "estimated_wait_minutes", "wait_time", "waiting_time"]);
const getServiceName = (s) => pick(s, ["name", "service_name", "title"]);
/* ----------------------------------------------------------------- */

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

function formatWait(value) {
  if (value === null || value === undefined) return "Ã¢â‚¬â€";
  if (typeof value === "number") return `${value} min`;
  return String(value);
}

export default function App() {
  const location = useLocation();
  const isStaffPage = location.pathname === "/staff";
  const [services, setServices] = useState([]);
  const [serviceId, setServiceId] = useState("");
  const [token, setToken] = useState(null);
  const [loadingServices, setLoadingServices] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(true);

  const [staffSession, setStaffSession] = useState(() => {
    try {
      const accessToken = sessionStorage.getItem("smartqueue_access_token");
      const staff = JSON.parse(sessionStorage.getItem("smartqueue_staff"));
      return accessToken && staff
        ? { access_token: accessToken, staff }
        : null;
    } catch {
      return null;
    }
  });

  const [staffUsername, setStaffUsername] = useState("");
  const [staffPassword, setStaffPassword] = useState("");
  const [staffLoginLoading, setStaffLoginLoading] = useState(false);
  const [staffLoginError, setStaffLoginError] = useState("");

  useEffect(() => {
    let active = true;
    request(ENDPOINTS.services)
      .then((data) => {
        if (!active) return;
        setServices(Array.isArray(data) ? data : []);
        setOnline(true);
      })
      .catch(() => {
        if (!active) return;
        setOnline(false);
        setError("Could not load campus services. Check that the backend is running, then reload the page.");
      })
      .finally(() => active && setLoadingServices(false));
    return () => {
      active = false;
    };
  }, []);

  async function loginStaff(event) {
    event.preventDefault();
    setStaffLoginError("");
    setStaffLoginLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: staffUsername.trim(),
          password: staffPassword,
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || `Login failed (${response.status})`);
      }

      if (!data?.access_token || !data?.staff) {
        throw new Error("The server returned an invalid login response.");
      }

      sessionStorage.setItem("smartqueue_access_token", data.access_token);
      sessionStorage.setItem("smartqueue_staff", JSON.stringify(data.staff));

      setStaffSession(data);
      setStaffPassword("");
    } catch (error) {
      setStaffLoginError(error.message || "Login failed. Please try again.");
    } finally {
      setStaffLoginLoading(false);
    }
  }

  function logoutStaff() {
    sessionStorage.removeItem("smartqueue_access_token");
    sessionStorage.removeItem("smartqueue_staff");
    setStaffSession(null);
    setStaffPassword("");
    setStaffLoginError("");
  }

  async function generateToken() {
    if (!serviceId) {
      setError("Select a campus service first.");
      return;
    }
    setError("");
    setGenerating(true);
    try {
      const created = await request(ENDPOINTS.createToken, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildTokenRequest(serviceId)),
      });
      const tokenNumber = getTokenNumber(created);
      if (tokenNumber === null) {
        setError("The server created a token but did not return its token number. Please try again.");
        return;
      }
      let latest = created;
      try {
        latest = { ...created, ...(await request(ENDPOINTS.tokenStatus(tokenNumber))) };
      } catch {
        /* keep the created token if the status call fails */
      }
      setToken(latest);
      setOnline(true);
    } catch {
      setOnline(false);
      setError("Your token could not be generated. Check your connection and try again.");
    } finally {
      setGenerating(false);
    }
  }

  async function refreshStatus() {
    const tokenNumber = token ? getTokenNumber(token) : null;
    if (tokenNumber === null) return;
    setError("");
    setRefreshing(true);
    try {
      const latest = await request(ENDPOINTS.tokenStatus(tokenNumber));
      setToken((prev) => ({ ...prev, ...latest }));
      setOnline(true);
    } catch {
      setOnline(false);
      setError("Queue status could not be refreshed. Try again in a moment.");
    } finally {
      setRefreshing(false);
    }
  }

  const ahead = token ? getAhead(token) : null;
  const status = token ? getStatus(token) : null;
  const isUnclaimed = status === "unclaimed";

  return (
    <div className="app" id="top">
      <header className="nav">
        <Link className="brand" to="/" aria-label="SmartQueue home">
          <span className="brand__mark">SQ</span>
          <span className="brand__name">SmartQueue</span>
        </Link>
        <nav className="nav__links" aria-label="Main">
          <Link to="/">Home</Link>
          <Link to="/">Student Portal</Link>
          <Link to="/staff">Staff Portal</Link>
        </nav>
        <p className={`pulse ${online ? "" : "pulse--off"}`} role="status">
          <span className="pulse__dot" aria-hidden="true" />
          {online ? "System Online" : "System Offline"}
        </p>
      </header>

      <main>
        {!isStaffPage && (
          <>
        <section className="hero">
          <div className="hero__photo" aria-hidden="true" />
          <div className="hero__tint" aria-hidden="true" />
          <div className="hero__shade" aria-hidden="true" />
          <div className="hero__grid" aria-hidden="true" />
          <span className="hero__circle" aria-hidden="true" />
          <span className="hero__block" aria-hidden="true" />

          <div className="hero__content">
            <h1 className="hero__title">
              <span className="hero__line hero__line--ivory">Skip the waiting.</span>
              <span className="hero__line hero__line--lemon">Know your place.</span>
            </h1>
            <p className="hero__lede">
              Generate your digital token and track your queue in real time.
            </p>
            <a className="btn btn--lemon" href="#portal">
              Get your token
            </a>
          </div>
        </section>

        <section className="portal" id="portal">
          <div className="portal__intro">
            <p className="tag">Student Portal</p>
            <h2 className="portal__title">Get your token</h2>
          </div>

          <div className="portal__panel">
            <div className="card card--form">
              <label className="field__label" htmlFor="service">
                Select campus service
              </label>
              <div className="select">
                <select
                  id="service"
                  value={serviceId}
                  onChange={(e) => setServiceId(e.target.value)}
                  disabled={loadingServices}
                >
                  <option value="">
                    {loadingServices ? "Loading servicesÃ¢â‚¬Â¦" : "Choose a service"}
                  </option>
                  {services.map((s) => (
                    <option key={pick(s, ["id", "service_id"])} value={pick(s, ["id", "service_id"])}>
                      {getServiceName(s)}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                className="btn btn--lemon btn--block"
                onClick={generateToken}
                disabled={generating || loadingServices}
              >
                {generating ? "GeneratingÃ¢â‚¬Â¦" : "Generate my token"}
              </button>

              {error && (
                <p className="alert" role="alert">
                  {error}
                </p>
              )}
            </div>

            {token && (
              <div className="card card--token" aria-live="polite">
                <p className="token__label">Your token</p>
                <p className="token__number">{getTokenNumber(token)}</p>

                {token.verification_code && (
                  <div className="token__verification">
                    <span>Verification number</span>
                    <strong>{token.verification_code}</strong>
                  </div>
                )}
                <div className="token__expiry">
                  <small>
                    Valid until: {token.expires_at
                      ? new Date(token.expires_at).toLocaleString("en-IN", {
                          timeZone: "Asia/Kolkata",
                          dateStyle: "medium",
                          timeStyle: "short",
                        })
                      : "Midnight IST"}
                  </small>
                </div>

                <dl className="token__facts">
                  <div>
                    <dt>Status</dt>
                    <dd>{isUnclaimed ? "Awaiting staff scan" : (status ?? "—")}</dd>
                  </div>
                  <div>
                    <dt>People ahead</dt>
                    <dd>{isUnclaimed ? "—" : (ahead ?? "—")}</dd>
                  </div>
                  <div>
                    <dt>Estimated waiting time</dt>
                    <dd>{isUnclaimed ? "—" : formatWait(getWait(token))}</dd>
                  </div>
                </dl>

                <button
                  type="button"
                  className="btn btn--lavender btn--block"
                  onClick={refreshStatus}
                  disabled={refreshing}
                >
                  {refreshing ? "RefreshingÃ¢â‚¬Â¦" : "Refresh queue status"}
                </button>
              </div>
            )}
          </div>
        </section>
          </>
        )}

        {isStaffPage && (staffSession ? (
          <StaffDashboard
            token={staffSession.access_token}
            staff={staffSession.staff}
            onLogout={logoutStaff}
          />
        ) : (
          <section className="portal" id="staff">
            <div className="portal__intro">
              <p className="tag">STAFF PORTAL</p>
              <h2 className="portal__title">Staff sign in</h2>
              <p>Authorized personnel only.</p>
            </div>

            <div className="portal__panel">
              <div className="card card--form">
                <form onSubmit={loginStaff}>
                  <label className="field__label" htmlFor="staff-username">
                    Username
                  </label>
                  <input
                    id="staff-username"
                    type="text"
                    autoComplete="username"
                    value={staffUsername}
                    onChange={(event) => setStaffUsername(event.target.value)}
                    required
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "14px",
                      marginBottom: "20px",
                      border: "2px solid #171717",
                      background: "#fff",
                      color: "#171717",
                      fontFamily: "inherit",
                      fontSize: "16px",
                    }}
                  />

                  <label className="field__label" htmlFor="staff-password">
                    Password
                  </label>
                  <input
                    id="staff-password"
                    type="password"
                    autoComplete="current-password"
                    value={staffPassword}
                    onChange={(event) => setStaffPassword(event.target.value)}
                    required
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "14px",
                      marginBottom: "20px",
                      border: "2px solid #171717",
                      background: "#fff",
                      color: "#171717",
                      fontFamily: "inherit",
                      fontSize: "16px",
                    }}
                  />

                  {staffLoginError && (
                    <p className="alert" role="alert">
                      {staffLoginError}
                    </p>
                  )}

                  <button
                    type="submit"
                    className="btn btn--lemon btn--block"
                    disabled={staffLoginLoading}
                  >
                    {staffLoginLoading ? "Signing in..." : "Sign in to Staff Portal"}
                  </button>
                </form>
              </div>
            </div>
          </section>
        ))}
      </main>

      <footer className="footer">
        <p className="footer__brand">SmartQueue</p>
        <p>Digital Queue Management and Waiting-Time Optimization System</p>
      </footer>
    </div>
  );
}





