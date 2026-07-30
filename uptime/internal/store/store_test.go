package store

import (
	"path/filepath"
	"testing"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/scheduler"
)

func open(t *testing.T) *Store {
	t.Helper()
	s, err := Open(filepath.Join(t.TempDir(), "test.db"))
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	t.Cleanup(func() { _ = s.Close() })
	return s
}

func TestStateRoundtrip(t *testing.T) {
	s := open(t)

	if _, found, err := s.LoadState("azzb"); err != nil || found {
		t.Fatalf("пустая база: found=%v err=%v", found, err)
	}

	want := scheduler.State{
		Status:      scheduler.StatusDown,
		Since:       time.Unix(1700000000, 0),
		ConsecFails: 4,
	}
	if err := s.SaveState("azzb", want); err != nil {
		t.Fatalf("SaveState: %v", err)
	}
	// Повторное сохранение — upsert, не ошибка.
	want.ConsecFails = 5
	if err := s.SaveState("azzb", want); err != nil {
		t.Fatalf("SaveState (update): %v", err)
	}

	got, found, err := s.LoadState("azzb")
	if err != nil || !found {
		t.Fatalf("LoadState: found=%v err=%v", found, err)
	}
	if got.Status != want.Status || !got.Since.Equal(want.Since) || got.ConsecFails != 5 {
		t.Errorf("got %+v, want %+v", got, want)
	}
}

func TestSummaryAndHistory(t *testing.T) {
	s := open(t)
	now := time.Now()

	// 3 успеха (латентности 100/200/300) и 1 неудача.
	for i, lat := range []time.Duration{100, 200, 300} {
		res := checker.Result{OK: true, HTTPStatus: 200, Latency: lat * time.Millisecond}
		if err := s.RecordCheck("azzb", now.Add(time.Duration(i)*time.Minute), res); err != nil {
			t.Fatalf("RecordCheck: %v", err)
		}
	}
	fail := checker.Result{HTTPStatus: 502, Err: "ожидали статус 200, получили 502"}
	if err := s.RecordCheck("azzb", now.Add(3*time.Minute), fail); err != nil {
		t.Fatalf("RecordCheck fail: %v", err)
	}

	sum, err := s.Summary("azzb", now.Add(-time.Hour))
	if err != nil {
		t.Fatalf("Summary: %v", err)
	}
	if sum.Count != 4 {
		t.Errorf("Count = %d, want 4", sum.Count)
	}
	if sum.UptimePct == nil || *sum.UptimePct != 75 {
		t.Errorf("UptimePct = %v, want 75", sum.UptimePct)
	}
	if sum.MedianLatencyMs == nil || *sum.MedianLatencyMs != 200 {
		t.Errorf("MedianLatencyMs = %v, want 200", sum.MedianLatencyMs)
	}

	// Период без данных — нет ни процента, ни медианы.
	empty, err := s.Summary("azzb", now.Add(time.Hour))
	if err != nil {
		t.Fatalf("Summary (пусто): %v", err)
	}
	if empty.Count != 0 || empty.UptimePct != nil || empty.MedianLatencyMs != nil {
		t.Errorf("пустой период: %+v", empty)
	}

	last, err := s.LastCheck("azzb")
	if err != nil || last == nil {
		t.Fatalf("LastCheck: %v, %v", last, err)
	}
	if last.OK || last.HTTPStatus != 502 {
		t.Errorf("последняя проверка не та: %+v", last)
	}

	hist, err := s.History("azzb", now.Add(-time.Hour), 10)
	if err != nil {
		t.Fatalf("History: %v", err)
	}
	if len(hist) != 4 || !hist[0].At.After(hist[3].At) {
		t.Errorf("History: len=%d, порядок свежие-первыми нарушен", len(hist))
	}
}

func TestCleanupBefore(t *testing.T) {
	s := open(t)
	now := time.Now()

	old := checker.Result{OK: true, HTTPStatus: 200}
	if err := s.RecordCheck("azzb", now.Add(-100*24*time.Hour), old); err != nil {
		t.Fatal(err)
	}
	if err := s.RecordCheck("azzb", now, old); err != nil {
		t.Fatal(err)
	}

	n, err := s.CleanupBefore(now.Add(-90 * 24 * time.Hour))
	if err != nil {
		t.Fatalf("CleanupBefore: %v", err)
	}
	if n != 1 {
		t.Errorf("удалено %d, want 1", n)
	}

	sum, _ := s.Summary("azzb", time.Unix(0, 0))
	if sum.Count != 1 {
		t.Errorf("осталось %d проверок, want 1", sum.Count)
	}
}
