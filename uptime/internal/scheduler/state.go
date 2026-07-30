package scheduler

import "time"

type Status string

const (
	StatusUnknown Status = "unknown"
	StatusUp      Status = "up"
	StatusDown    Status = "down"
)

type State struct {
	Status      Status
	Since       time.Time
	ConsecFails int
}

func NewState(at time.Time) State {
	return State{Status: StatusUnknown, Since: at}
}

// Transition — смена статуса монитора.
type Transition struct {
	From    Status
	To      Status
	At      time.Time
	DownFor time.Duration // сколько лежал; заполнено при переходе down → up
}

// Apply применяет результат проверки; статус меняется на down только после
// failuresToDown подряд неудач (защита от флапов), на up — после первой удачи.
func Apply(s State, ok bool, at time.Time, failuresToDown int) (State, *Transition) {
	if ok {
		s.ConsecFails = 0
		if s.Status == StatusUp {
			return s, nil
		}
		tr := &Transition{From: s.Status, To: StatusUp, At: at}
		if s.Status == StatusDown {
			tr.DownFor = at.Sub(s.Since)
		}
		s.Status = StatusUp
		s.Since = at
		return s, tr
	}

	s.ConsecFails++
	if s.Status != StatusDown && s.ConsecFails >= failuresToDown {
		tr := &Transition{From: s.Status, To: StatusDown, At: at}
		s.Status = StatusDown
		s.Since = at
		return s, tr
	}
	return s, nil
}
