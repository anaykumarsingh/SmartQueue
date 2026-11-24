import { useCallback, useEffect, useState } from "react";
import "./StaffDashboard.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Some responses may not contain JSON.
  }

  if (!response.ok) {
    throw new Error(data?.detail || `Request failed (${response.status})`);
  }

  return data;
}

export default function StaffDashboard({ token, staff, onLogout }) {
  const [counters, setCounters] = useState([]);
  const [selectedCounterId, setSelectedCounterId] = useState("");
  const [display, setDisplay] = useState(null);
  const [loadingCounters, setLoadingCounters] = useState(true);
  const [loadingDisplay, setLoadingDisplay] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verifiedTicket, setVerifiedTicket] = useState(null);
  const [scanBusy, setScanBusy] = useState(false);

  useEffect(() => {
    let active = true;

    apiRequest("/counters/")
      .then((data) => {
        if (!active) return;

        const list = Array.isArray(data) ? data : [];
        setCounters(list);

        const firstAvailable = list.find((counter) => counter.status === "open") || list[0];

        if (firstAvailable) {
          setSelectedCounterId(String(firstAvailable.id));
        }
      })
      .catch((err) => {
        if (active) setError(err.message || "Could not load counters.");
      })
      .finally(() => {
        if (active) setLoadingCounters(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedCounter = counters.find(
    (counter) => String(counter.id) === String(selectedCounterId)
  );

  const loadDisplay = useCallback(async () => {
    if (!selectedCounter) return;

    setLoadingDisplay(true);

    try {
      const data = await apiRequest(`/display/${selectedCounter.service_id}`);
      setDisplay(data);
      setError("");
    } catch (err) {
      setError(err.message || "Could not load queue information.");
    } finally {
      setLoadingDisplay(false);
    }
  }, [selectedCounter?.service_id]);

  useEffect(() => {
    loadDisplay();

    const refreshInterval = setInterval(() => {
      loadDisplay();
    }, 5000);

    return () => clearInterval(refreshInterval);
  }, [loadDisplay]);

  const ticketMatchesService =
    verifiedTicket &&
    Number(verifiedTicket.service_id) === Number(selectedCounter?.service_id);

  async function verifyTicket() {
    if (!selectedCounterId || !ticketNumber.trim() || !/^\d{6}$/.test(verificationCode)) {
      setError("Enter a ticket number and a valid six-digit verification code.");
      return;
    }

    setScanBusy(true);
    setVerifiedTicket(null);
    setError("");
    setMessage("");

    try {
      const result = await apiRequest("/staff/verify-ticket", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          token_number: ticketNumber.trim(),
          verification_code: verificationCode,
          counter_id: Number(selectedCounterId),
        }),
      });

      setVerifiedTicket(result);
    } catch (err) {
      setError(err.message || "Ticket verification failed.");
    } finally {
      setScanBusy(false);
    }
  }

  async function confirmTicketClaim() {
    if (!verifiedTicket || !ticketMatchesService) return;

    setActionLoading(true);
    setError("");
    setMessage("");

    try {
      const result = await apiRequest("/staff/claim-ticket", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          token_number: ticketNumber.trim(),
          verification_code: verificationCode,
          counter_id: Number(selectedCounterId),
        }),
      });

      setMessage(`${result.token_number} successfully added to the queue.`);
      setVerifiedTicket(null);
      setTicketNumber("");
      setVerificationCode("");
      await loadDisplay();
    } catch (err) {
      setError(err.message || "Could not claim this ticket.");
    } finally {
      setActionLoading(false);
    }
  }

  const currentToken = display?.currently_serving?.find(
    (token) => token.counter_label === selectedCounter?.label
  );

  const waitingTokens = display?.waiting_tokens || [];

  async function performAction(action) {
    if (!selectedCounter) return;

    setActionLoading(true);
    setError("");
    setMessage("");

    try {
      const result = await apiRequest(`/staff/${action}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          counter_id: Number(selectedCounter.id),
        }),
      });

      const tokenNumber = result?.token_number || "Token";
      setMessage(
        action === "call-next"
          ? `${tokenNumber} is now being served.`
          : `${tokenNumber} has been completed.`
      );

      await loadDisplay();
    } catch (err) {
      setError(err.message || "The operation could not be completed.");
      await loadDisplay();
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="staff-dashboard" id="staff">
      <div className="staff-heading">
        <div>
          <p className="staff-eyebrow">STAFF CONTROL ROOM</p>
          <h2>Manage the queue.</h2>
          <p className="staff-description">
            Call the next student, complete service, and monitor your counter.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
          <span className="staff-live">
            <span className="staff-live-dot" />
            Queue management
          </span>
          <span style={{ fontSize: "14px" }}>
            {staff?.full_name || staff?.username}
          </span>
          <button
            type="button"
            className="staff-refresh"
            onClick={onLogout}
          >
            Log out
          </button>
        </div>
      </div>

      <div className="staff-toolbar">
        <div className="staff-field">
          <label htmlFor="staff-counter">Select your counter</label>
          <select
            id="staff-counter"
            value={selectedCounterId}
            onChange={(event) => {
              setSelectedCounterId(event.target.value);
              setVerifiedTicket(null);
              setTicketNumber("");
              setVerificationCode("");
              setMessage("");
              setError("");
            }}
            disabled={loadingCounters || counters.length === 0}
          >
            {loadingCounters && <option value="">Loading counters...</option>}
            {!loadingCounters && counters.length === 0 && (
              <option value="">No counters available</option>
            )}
            {counters.map((counter) => (
              <option key={counter.id} value={counter.id}>
                {counter.label} — {counter.status}
              </option>
            ))}
          </select>
        </div>

        <button
          className="staff-refresh"
          type="button"
          onClick={loadDisplay}
          disabled={!selectedCounter || loadingDisplay || actionLoading}
        >
          {loadingDisplay ? "Refreshing..." : "Refresh queue"}
        </button>
      </div>

      {selectedCounter && (
        <>
          <div className="staff-summary">
            <div className="staff-summary-card">
              <span className="staff-card-label">SELECTED SERVICE</span>
              <strong>{display?.service_name || "Loading..."}</strong>
            </div>

            <div className="staff-summary-card">
              <span className="staff-card-label">COUNTER STATUS</span>
              <strong className={selectedCounter.status === "open" ? "staff-open" : "staff-closed"}>
                {selectedCounter.status.toUpperCase()}
              </strong>
            </div>

            <div className="staff-summary-card">
              <span className="staff-card-label">PEOPLE WAITING</span>
              <strong>{display?.total_waiting ?? "—"}</strong>
            </div>
          </div>

          <div className="staff-scanner-panel">
            <div className="staff-scanner-heading">
              <div>
                <p className="staff-card-label">TICKET VERIFICATION</p>
                <h3>Verify student ticket</h3>
                <p>Enter the ticket number and the six-digit code shown on the student's ticket.</p>
              </div>
            </div>

            <form
              className="staff-manual-form"
              onSubmit={(event) => {
                event.preventDefault();
                verifyTicket();
              }}
            >
              <div className="staff-manual-field">
                <label htmlFor="staff-ticket-number">Ticket number</label>
                <input
                  id="staff-ticket-number"
                  type="text"
                  placeholder="e.g. LIB_007"
                  value={ticketNumber}
                  onChange={(event) => {
                    setTicketNumber(event.target.value.toUpperCase());
                    setVerifiedTicket(null);
                    setError("");
                  }}
                  autoComplete="off"
                  required
                />
              </div>

              <div className="staff-manual-field">
                <label htmlFor="staff-verification-code">Six-digit verification code</label>
                <input
                  id="staff-verification-code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  placeholder="Enter 6-digit code"
                  value={verificationCode}
                  onChange={(event) => {
                    setVerificationCode(event.target.value.replace(/\D/g, "").slice(0, 6));
                    setVerifiedTicket(null);
                    setError("");
                  }}
                  autoComplete="off"
                  required
                />
              </div>

              <button
                type="submit"
                className="staff-button staff-button-secondary"
                disabled={scanBusy || actionLoading || !selectedCounterId}
              >
                {scanBusy ? "Verifying..." : "Verify Ticket"}
              </button>
            </form>

            {verifiedTicket && (
              <div className="staff-verified-ticket">
                <p className="staff-card-label">TICKET VERIFIED</p>
                <strong>{verifiedTicket.token_number}</strong>
                <span>Service: {verifiedTicket.service_name}</span>
                <span>Status: {verifiedTicket.status}</span>

                {!ticketMatchesService && (
                  <p className="staff-scan-warning">
                    This ticket belongs to a different service. Select the matching counter before claiming it.
                  </p>
                )}

                <button
                  type="button"
                  className="staff-button staff-button-primary"
                  onClick={confirmTicketClaim}
                  disabled={!ticketMatchesService || actionLoading || scanBusy}
                >
                  {actionLoading ? "Claiming..." : "Confirm Claim"}
                </button>
              </div>
            )}
          </div>
          <div className="staff-workspace">
            <div className="staff-current">
              <p className="staff-card-label">CURRENTLY SERVING</p>

              {currentToken ? (
                <div className="staff-current-token">
                  <span>NOW SERVING</span>
                  <strong>{currentToken.token_number}</strong>
                  <p>{selectedCounter.label}</p>
                </div>
              ) : (
                <div className="staff-empty">
                  <strong>No active token</strong>
                  <p>This counter is not serving anyone right now.</p>
                </div>
              )}

              <div className="staff-actions">
                <button
                  type="button"
                  className="staff-button staff-button-primary"
                  onClick={() => performAction("call-next")}
                  disabled={
                    actionLoading ||
                    selectedCounter.status !== "open" ||
                    Boolean(currentToken) ||
                    waitingTokens.length === 0
                  }
                >
                  {actionLoading ? "Please wait..." : "Call next student"}
                </button>

                <button
                  type="button"
                  className="staff-button staff-button-secondary"
                  onClick={() => performAction("complete")}
                  disabled={
                    actionLoading ||
                    selectedCounter.status !== "open" ||
                    !currentToken
                  }
                >
                  Complete current token
                </button>
              </div>
            </div>

            <div className="staff-queue">
              <div className="staff-queue-heading">
                <div>
                  <p className="staff-card-label">UP NEXT</p>
                  <h3>Waiting queue</h3>
                </div>
                <span>{waitingTokens.length} waiting</span>
              </div>

              {waitingTokens.length > 0 ? (
                <div className="staff-queue-list">
                  {waitingTokens.map((token) => (
                    <div className="staff-queue-row" key={token.token_number}>
                      <span className="staff-position">
                        {String(token.position).padStart(2, "0")}
                      </span>
                      <strong>{token.token_number}</strong>
                      <span className="staff-waiting-label">Waiting</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="staff-empty staff-queue-empty">
                  <strong>The queue is clear.</strong>
                  <p>There are no students waiting for this service.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {error && <p className="staff-alert" role="alert">{error}</p>}
      {message && <p className="staff-success" role="status">{message}</p>}
    </section>
  );
}






