package scheduler

import (
	"testing"
	"time"
)

func TestApplyTransitions(t *testing.T) {
	t0 := time.Date(2026, 7, 30, 12, 0, 0, 0, time.UTC)
	const failsToDown = 3

	st := NewState(t0)

	// Стартовый unknown → up после первой удачи.
	st, tr := Apply(st, true, t0.Add(time.Minute), failsToDown)
	if tr == nil || tr.From != StatusUnknown || tr.To != StatusUp {
		t.Fatalf("ждали переход unknown→up, получили %+v", tr)
	}

	// Одна-две неудачи — ещё не down (защита от флапов).
	st, tr = Apply(st, false, t0.Add(2*time.Minute), failsToDown)
	if tr != nil {
		t.Fatalf("переход после 1-й неудачи: %+v", tr)
	}
	st, tr = Apply(st, false, t0.Add(3*time.Minute), failsToDown)
	if tr != nil || st.ConsecFails != 2 {
		t.Fatalf("после 2-й неудачи: tr=%+v fails=%d", tr, st.ConsecFails)
	}

	// Третья подряд — down.
	downAt := t0.Add(4 * time.Minute)
	st, tr = Apply(st, false, downAt, failsToDown)
	if tr == nil || tr.From != StatusUp || tr.To != StatusDown {
		t.Fatalf("ждали up→down, получили %+v", tr)
	}
	if st.Since != downAt {
		t.Errorf("Since = %v, want %v", st.Since, downAt)
	}

	// Дальнейшие неудачи не порождают повторных переходов (нет спама).
	st, tr = Apply(st, false, t0.Add(5*time.Minute), failsToDown)
	if tr != nil {
		t.Fatalf("повторный переход в down: %+v", tr)
	}

	// Первая удача — up, в переходе длительность простоя.
	upAt := t0.Add(16 * time.Minute)
	st, tr = Apply(st, true, upAt, failsToDown)
	if tr == nil || tr.From != StatusDown || tr.To != StatusUp {
		t.Fatalf("ждали down→up, получили %+v", tr)
	}
	if tr.DownFor != 12*time.Minute {
		t.Errorf("DownFor = %v, want 12m", tr.DownFor)
	}
	if st.ConsecFails != 0 {
		t.Errorf("ConsecFails = %d, want 0", st.ConsecFails)
	}
}

func TestApplyUnknownToDown(t *testing.T) {
	t0 := time.Now()
	st := NewState(t0)

	var tr *Transition
	for i := 1; i <= 3; i++ {
		st, tr = Apply(st, false, t0.Add(time.Duration(i)*time.Minute), 3)
	}
	if tr == nil || tr.From != StatusUnknown || tr.To != StatusDown {
		t.Fatalf("ждали unknown→down после 3 неудач, получили %+v", tr)
	}
}

func TestApplyUpStaysUp(t *testing.T) {
	t0 := time.Now()
	st := State{Status: StatusUp, Since: t0}

	st, tr := Apply(st, true, t0.Add(time.Minute), 3)
	if tr != nil {
		t.Fatalf("переход при up+ok: %+v", tr)
	}
	if st.Since != t0 {
		t.Errorf("Since сдвинулся без перехода: %v", st.Since)
	}
}
