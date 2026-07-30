// Package store — SQLite-хранилище проверок и состояний мониторов.
package store

import (
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	_ "modernc.org/sqlite" // драйвер database/sql без CGO

	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
)

const schema = `
CREATE TABLE IF NOT EXISTS checks (
	id INTEGER PRIMARY KEY,
	monitor_slug TEXT NOT NULL,
	ts INTEGER NOT NULL,
	ok INTEGER NOT NULL,
	http_status INTEGER NOT NULL DEFAULT 0,
	latency_ms INTEGER NOT NULL DEFAULT 0,
	error TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_checks_slug_ts ON checks(monitor_slug, ts);
CREATE TABLE IF NOT EXISTS state (
	monitor_slug TEXT PRIMARY KEY,
	status TEXT NOT NULL,
	since INTEGER NOT NULL,
	consec_fails INTEGER NOT NULL
);
`

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	if dir := filepath.Dir(path); dir != "." && dir != "" {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, fmt.Errorf("каталог БД: %w", err)
		}
	}
	db, err := sql.Open("sqlite", "file:"+path+"?_pragma=journal_mode(WAL)&_pragma=busy_timeout(5000)")
	if err != nil {
		return nil, err
	}
	// Один писатель: сериализуем доступ на уровне пула — никаких SQLITE_BUSY.
	db.SetMaxOpenConns(1)
	if _, err := db.Exec(schema); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("миграция схемы: %w", err)
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) RecordCheck(slug string, at time.Time, res checker.Result) error {
	_, err := s.db.Exec(
		`INSERT INTO checks (monitor_slug, ts, ok, http_status, latency_ms, error)
		 VALUES (?, ?, ?, ?, ?, ?)`,
		slug, at.Unix(), boolToInt(res.OK), res.HTTPStatus, res.Latency.Milliseconds(), res.Err,
	)
	return err
}

func (s *Store) LoadState(slug string) (scheduler.State, bool, error) {
	var (
		status string
		since  int64
		fails  int
	)
	err := s.db.QueryRow(
		`SELECT status, since, consec_fails FROM state WHERE monitor_slug = ?`, slug,
	).Scan(&status, &since, &fails)
	if errors.Is(err, sql.ErrNoRows) {
		return scheduler.State{}, false, nil
	}
	if err != nil {
		return scheduler.State{}, false, err
	}
	return scheduler.State{
		Status:      scheduler.Status(status),
		Since:       time.Unix(since, 0),
		ConsecFails: fails,
	}, true, nil
}

func (s *Store) SaveState(slug string, st scheduler.State) error {
	_, err := s.db.Exec(
		`INSERT INTO state (monitor_slug, status, since, consec_fails)
		 VALUES (?, ?, ?, ?)
		 ON CONFLICT(monitor_slug) DO UPDATE SET
		   status = excluded.status, since = excluded.since, consec_fails = excluded.consec_fails`,
		slug, string(st.Status), st.Since.Unix(), st.ConsecFails,
	)
	return err
}

// Summary — агрегат за период: доля успешных проверок и медианная латентность.
type Summary struct {
	Count           int
	UptimePct       *float64
	MedianLatencyMs *int64
}

func (s *Store) Summary(slug string, since time.Time) (Summary, error) {
	var (
		count int
		okSum sql.NullInt64
	)
	err := s.db.QueryRow(
		`SELECT COUNT(*), SUM(ok) FROM checks WHERE monitor_slug = ? AND ts >= ?`,
		slug, since.Unix(),
	).Scan(&count, &okSum)
	if err != nil {
		return Summary{}, err
	}
	out := Summary{Count: count}
	if count > 0 {
		pct := float64(okSum.Int64) / float64(count) * 100
		out.UptimePct = &pct
	}

	var median int64
	err = s.db.QueryRow(
		`SELECT latency_ms FROM checks
		 WHERE monitor_slug = ? AND ts >= ? AND ok = 1
		 ORDER BY latency_ms
		 LIMIT 1 OFFSET (
			SELECT (COUNT(*) - 1) / 2 FROM checks
			WHERE monitor_slug = ? AND ts >= ? AND ok = 1
		 )`,
		slug, since.Unix(), slug, since.Unix(),
	).Scan(&median)
	switch {
	case errors.Is(err, sql.ErrNoRows):
		// ни одной успешной проверки — медианы нет
	case err != nil:
		return Summary{}, err
	default:
		out.MedianLatencyMs = &median
	}
	return out, nil
}

type CheckRow struct {
	At         time.Time
	OK         bool
	HTTPStatus int
	LatencyMs  int64
	Error      string
}

func (s *Store) LastCheck(slug string) (*CheckRow, error) {
	rows, err := s.History(slug, time.Unix(0, 0), 1)
	if err != nil || len(rows) == 0 {
		return nil, err
	}
	return &rows[0], nil
}

// History возвращает проверки новее since, свежие первыми.
func (s *Store) History(slug string, since time.Time, limit int) ([]CheckRow, error) {
	rows, err := s.db.Query(
		`SELECT ts, ok, http_status, latency_ms, error FROM checks
		 WHERE monitor_slug = ? AND ts >= ?
		 ORDER BY ts DESC LIMIT ?`,
		slug, since.Unix(), limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []CheckRow
	for rows.Next() {
		var (
			r  CheckRow
			ts int64
			ok int
		)
		if err := rows.Scan(&ts, &ok, &r.HTTPStatus, &r.LatencyMs, &r.Error); err != nil {
			return nil, err
		}
		r.At = time.Unix(ts, 0)
		r.OK = ok == 1
		out = append(out, r)
	}
	return out, rows.Err()
}

// CleanupBefore удаляет проверки старше t (ретенция).
func (s *Store) CleanupBefore(t time.Time) (int64, error) {
	res, err := s.db.Exec(`DELETE FROM checks WHERE ts < ?`, t.Unix())
	if err != nil {
		return 0, err
	}
	return res.RowsAffected()
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
