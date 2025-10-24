import React, { useEffect, useState } from 'react';

export default function Swapfest() {
  const [prizePool, setPrizePool] = useState(0);
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    fetch('https://mvponflow.cc/api/leaderboard')
      .then(res => res.json())
      .then(data => {
        setPrizePool(data.prize_pool);
        setLeaderboard(data.leaderboard || []);
      });
  }, []);

  const formatTs = (ts) => {
    if (!ts) return '-';
    // API returns "YYYY-MM-DD HH:MM:SS" (UTC). Treat as UTC.
    // Convert to user local time and show a short, readable string.
    try {
      // Replace space with 'T' and add 'Z' to mark UTC
      const iso = ts.includes('T') ? ts : ts.replace(' ', 'T') + 'Z';
      const d = new Date(iso);
      return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).format(d);
    } catch {
      return ts; // fallback to raw string
    }
  };

  return (
    <div className="container">
      <div className="card shadow mb-4">
        <div className="card-body">
          <h2 className="mb-4 text-center">🏀 $MVP Season Start Swap Fest Ending Oct 21st 🏆</h2>

          <div className="text-center mb-4">
            <img
              src="/images/25-8-15-9-25.png"
              alt="Swap Fest Rules"
              className="img-fluid rounded shadow"
            />
          </div>

          <p className="text-center mb-3">
            Prize Pool: {prizePool} chances to pet your horse
          </p>

          <div className="table-responsive">
            <table className="mvp-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>TopShot Username</th>
                  <th>Points</th>
                  <th>Last scored at</th>
                  <th>Prize</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>{entry.username}</td>
                    <td>{entry.points}</td>
                    <td>{formatTs(entry.last_scored_at)}</td>
                    <td>{entry.prize}</td>
                  </tr>
                ))}
                {leaderboard.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '1rem' }}>
                      No entries yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="text-muted mt-2" style={{ fontSize: '0.9rem' }}>
            * Ties on points are ranked by earlier “Last scored at”.
          </div>
        </div>
      </div>
    </div>
  );
}
