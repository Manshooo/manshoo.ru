// Package scheduler крутит циклы проверок мониторов и ведёт их состояние.
package scheduler

import (
	"context"
	"log/slog"
	"math/rand/v2"
	"sync"
	"time"

	"github.com/Manshooo/manshoo.ru/uptime/internal/checker"
	"github.com/Manshooo/manshoo.ru/uptime/internal/config"
)

// retryInterval — ускоренная перепроверка, пока монитор «шатается»:
// неудачи уже есть, но статус ещё не down. Сжимает время обнаружения.
const retryInterval = 15 * time.Second

type Store interface {
	RecordCheck(slug string, at time.Time, res checker.Result) error
	LoadState(slug string) (State, bool, error)
	SaveState(slug string, s State) error
}

// Event — событие смены статуса для уведомлений.
type Event struct {
	Monitor config.Monitor
	Tr      Transition
	Reason  string // причина последней неудачной проверки (для алерта о падении)
}

type Notifier interface {
	Notify(ctx context.Context, e Event)
}

type Runner struct {
	cfg      *config.Config
	checker  *checker.Checker
	store    Store
	notifier Notifier
	log      *slog.Logger
}

func NewRunner(cfg *config.Config, c *checker.Checker, s Store, n Notifier, log *slog.Logger) *Runner {
	return &Runner{cfg: cfg, checker: c, store: s, notifier: n, log: log}
}

// Run запускает по горутине на монитор и блокируется до отмены ctx.
func (r *Runner) Run(ctx context.Context) {
	var wg sync.WaitGroup
	for _, m := range r.cfg.Monitors {
		wg.Add(1)
		go func() {
			defer wg.Done()
			r.runMonitor(ctx, m)
		}()
	}
	wg.Wait()
}

func (r *Runner) runMonitor(ctx context.Context, m config.Monitor) {
	st, found, err := r.store.LoadState(m.Slug)
	if err != nil {
		r.log.Error("load state", "monitor", m.Slug, "err", err)
	}
	if !found {
		st = NewState(time.Now())
	}

	// Джиттер, чтобы мониторы не стреляли одновременно.
	if !sleepCtx(ctx, time.Duration(rand.N(int64(3*time.Second)))) {
		return
	}

	for {
		st = r.tick(ctx, m, st)

		delay := m.Interval.Std()
		if st.ConsecFails > 0 && st.Status != StatusDown {
			delay = min(retryInterval, delay)
		}
		if !sleepCtx(ctx, delay) {
			return
		}
	}
}

func (r *Runner) tick(ctx context.Context, m config.Monitor, st State) State {
	res := r.checker.Check(ctx, m)
	if ctx.Err() != nil {
		// Проверка оборвана остановкой сервиса — не записываем ложную неудачу.
		return st
	}
	at := time.Now()
	if err := r.store.RecordCheck(m.Slug, at, res); err != nil {
		r.log.Error("record check", "monitor", m.Slug, "err", err)
	}

	newSt, tr := Apply(st, res.OK, at, m.FailuresToDown)
	if tr == nil {
		if newSt.ConsecFails != st.ConsecFails {
			// Счётчик неудач переживает рестарт — сохраняем и без перехода.
			if err := r.store.SaveState(m.Slug, newSt); err != nil {
				r.log.Error("save state", "monitor", m.Slug, "err", err)
			}
		}
		return newSt
	}

	if err := r.store.SaveState(m.Slug, newSt); err != nil {
		r.log.Error("save state", "monitor", m.Slug, "err", err)
	}
	r.log.Info("status change", "monitor", m.Slug, "from", tr.From, "to", tr.To)

	// Стартовый unknown → up — не событие, алертов не шлём.
	if tr.From != StatusUnknown || tr.To != StatusUp {
		r.notifier.Notify(ctx, Event{Monitor: m, Tr: *tr, Reason: res.Err})
	}
	return newSt
}

// sleepCtx ждёт d; false — если ctx отменили раньше.
func sleepCtx(ctx context.Context, d time.Duration) bool {
	select {
	case <-ctx.Done():
		return false
	case <-time.After(d):
		return true
	}
}
