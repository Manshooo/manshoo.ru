package checker

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/url"
	"time"
)

// TLSInfo — что удалось узнать о сертификате цели.
type TLSInfo struct {
	NotAfter  time.Time
	DaysLeft  int
	CheckedAt time.Time
}

// CheckTLS смотрит срок сертификата. Для http-целей возвращает (nil, nil):
// проверять нечего, это не ошибка.
func CheckTLS(ctx context.Context, rawURL string) (*TLSInfo, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return nil, fmt.Errorf("разбор url: %w", err)
	}
	if u.Scheme != "https" {
		return nil, nil
	}

	host := u.Hostname()
	port := u.Port()
	if port == "" {
		port = "443"
	}

	// InsecureSkipVerify: нам нужна только дата истечения. С включённой
	// проверкой цепочки рукопожатие обрывалось бы как раз в интересном
	// случае — когда сертификат уже просрочен, и мы не узнали бы, насколько.
	// Валидность цепочки и так проверяет обычная HTTP-проверка монитора.
	dialer := &tls.Dialer{Config: &tls.Config{
		ServerName:         host,
		MinVersion:         tls.VersionTLS12,
		InsecureSkipVerify: true, //nolint:gosec // см. комментарий выше
	}}
	conn, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(host, port))
	if err != nil {
		return nil, fmt.Errorf("tls-соединение: %w", err)
	}
	defer func() { _ = conn.Close() }()

	certs := conn.(*tls.Conn).ConnectionState().PeerCertificates
	if len(certs) == 0 {
		return nil, fmt.Errorf("сервер не прислал сертификат")
	}

	now := time.Now()
	notAfter := certs[0].NotAfter
	return &TLSInfo{
		NotAfter:  notAfter,
		DaysLeft:  int(notAfter.Sub(now).Hours() / 24),
		CheckedAt: now,
	}, nil
}
