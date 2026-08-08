// Package config читает и валидирует YAML-конфигурацию мониторов.
package config

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// Duration — обёртка над time.Duration, парсит строки вида "60s" из YAML.
type Duration time.Duration

func (d *Duration) UnmarshalYAML(node *yaml.Node) error {
	var raw string
	if err := node.Decode(&raw); err != nil {
		return err
	}
	parsed, err := time.ParseDuration(raw)
	if err != nil {
		return fmt.Errorf("некорректная длительность %q: %w", raw, err)
	}
	*d = Duration(parsed)
	return nil
}

func (d Duration) Std() time.Duration { return time.Duration(d) }

type Defaults struct {
	Interval       Duration `yaml:"interval"`
	Timeout        Duration `yaml:"timeout"`
	FailuresToDown int      `yaml:"failures_to_down"`
	// За сколько дней до истечения сертификата предупреждать (0 — не следить)
	TLSExpiryWarnDays int `yaml:"tls_expiry_warn_days"`
}

// Heartbeat — пинг внешнего dead-man's-switch. URL берётся из env
// (HEARTBEAT_URL), потому что это секрет: кто знает ссылку, тот может
// заглушить тревогу.
type Heartbeat struct {
	URL      string
	Interval Duration `yaml:"heartbeat_interval"`
}

type Monitor struct {
	Slug           string   `yaml:"slug"`
	Name           string   `yaml:"name"`
	URL            string   `yaml:"url"`
	Interval       Duration `yaml:"interval"`
	Timeout        Duration `yaml:"timeout"`
	ExpectStatus   int      `yaml:"expect_status"`
	FailuresToDown int      `yaml:"failures_to_down"`
}

type Config struct {
	Defaults  Defaults  `yaml:"defaults"`
	Monitors  []Monitor `yaml:"monitors"`
	Heartbeat Heartbeat `yaml:"-"`
}

func Load(path string) (*Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("чтение конфига: %w", err)
	}
	return Parse(raw)
}

func Parse(raw []byte) (*Config, error) {
	var cfg Config
	dec := yaml.NewDecoder(bytes.NewReader(raw))
	dec.KnownFields(true)
	if err := dec.Decode(&cfg); err != nil && !errors.Is(err, io.EOF) {
		return nil, fmt.Errorf("разбор конфига: %w", err)
	}

	if cfg.Defaults.Interval == 0 {
		cfg.Defaults.Interval = Duration(60 * time.Second)
	}
	if cfg.Defaults.Timeout == 0 {
		cfg.Defaults.Timeout = Duration(10 * time.Second)
	}
	if cfg.Defaults.FailuresToDown == 0 {
		cfg.Defaults.FailuresToDown = 3
	}
	if cfg.Defaults.TLSExpiryWarnDays == 0 {
		cfg.Defaults.TLSExpiryWarnDays = 14
	}

	cfg.Heartbeat.URL = os.Getenv("HEARTBEAT_URL")
	if cfg.Heartbeat.Interval == 0 {
		cfg.Heartbeat.Interval = Duration(5 * time.Minute)
	}

	if len(cfg.Monitors) == 0 {
		return nil, errors.New("в конфиге нет ни одного монитора")
	}

	seen := make(map[string]bool, len(cfg.Monitors))
	for i := range cfg.Monitors {
		m := &cfg.Monitors[i]
		if m.Slug == "" {
			return nil, fmt.Errorf("монитор №%d: пустой slug", i+1)
		}
		if seen[m.Slug] {
			return nil, fmt.Errorf("монитор %q: slug повторяется", m.Slug)
		}
		seen[m.Slug] = true
		if m.Name == "" {
			m.Name = m.Slug
		}
		u, err := url.Parse(m.URL)
		if err != nil || (u.Scheme != "http" && u.Scheme != "https") || u.Host == "" {
			return nil, fmt.Errorf("монитор %q: некорректный url %q", m.Slug, m.URL)
		}
		if m.Interval == 0 {
			m.Interval = cfg.Defaults.Interval
		}
		if m.Interval.Std() < 5*time.Second {
			return nil, fmt.Errorf("монитор %q: interval меньше 5s", m.Slug)
		}
		if m.Timeout == 0 {
			m.Timeout = cfg.Defaults.Timeout
		}
		if m.ExpectStatus == 0 {
			m.ExpectStatus = 200
		}
		if m.FailuresToDown == 0 {
			m.FailuresToDown = cfg.Defaults.FailuresToDown
		}
	}
	return &cfg, nil
}
