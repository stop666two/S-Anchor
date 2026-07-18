package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

const (
	pyScript   = "server.py"
	pyPort     = "9001"
	pyHost     = "http://127.0.0.1:" + pyPort
	maxWorkers = 3
	reqTimeout = 10 * time.Second
	burstLimit = 10
)

type WorkerPool struct {
	mu       sync.Mutex
	cond     *sync.Cond
	capacity int
	active   int
}

func NewWorkerPool(cap int) *WorkerPool {
	p := &WorkerPool{capacity: cap}
	p.cond = sync.NewCond(&p.mu)
	return p
}

func (p *WorkerPool) Acquire() {
	p.mu.Lock()
	for p.active >= p.capacity {
		p.cond.Wait()
	}
	p.active++
	p.mu.Unlock()
}

func (p *WorkerPool) Release() {
	p.mu.Lock()
	p.active--
	p.cond.Signal()
	p.mu.Unlock()
}

type tokenBucket struct {
	mu       sync.Mutex
	tokens   int
	limit    int
	interval time.Duration
	lastFill time.Time
}

func newTokenBucket(limit int, interval time.Duration) *tokenBucket {
	return &tokenBucket{
		tokens:   limit,
		limit:    limit,
		interval: interval,
		lastFill: time.Now(),
	}
}

func (tb *tokenBucket) allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	now := time.Now()
	elapsed := now.Sub(tb.lastFill)
	n := int(elapsed / tb.interval)
	accounted := time.Duration(n) * tb.interval
	tb.lastFill = tb.lastFill.Add(accounted)
	tb.tokens += n
	if tb.tokens > tb.limit {
		tb.tokens = tb.limit
	}
	if tb.tokens > 0 {
		tb.tokens--
		return true
	}
	return false
}

type EmbedRequest struct {
	ImageB64      string  `json:"image_b64"`
	WatermarkText string  `json:"watermark_text"`
	Alpha         float64 `json:"alpha"`
	Delta         float64 `json:"delta"`
	Level         int     `json:"level"`
	SyncEnabled   bool    `json:"sync_enabled"`
	BchEnabled    bool    `json:"bch_enabled"`
}

type ExtractRequest struct {
	ImageB64    string  `json:"image_b64"`
	Delta       float64 `json:"delta"`
	Level       int     `json:"level"`
	SyncEnabled bool    `json:"sync_enabled"`
	BchEnabled  bool    `json:"bch_enabled"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	RetryIn int    `json:"retry_in,omitempty"`
}

var (
	workerPool = NewWorkerPool(maxWorkers)
	rateLimiter = newTokenBucket(burstLimit, 100*time.Millisecond)
)

func proxyToPython(w http.ResponseWriter, r *http.Request, path string, body io.Reader) {
	if !rateLimiter.allow() {
		writeJSON(w, http.StatusTooManyRequests, ErrorResponse{Error: "rate limit exceeded", RetryIn: 1})
		return
	}

	workerPool.Acquire()
	defer workerPool.Release()

	ctx := r.Context()
	req, err := http.NewRequestWithContext(ctx, r.Method, pyHost+path, body)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal error")
		return
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: reqTimeout}
	resp, err := client.Do(req)
	if err != nil {
		writeJSON(w, http.StatusGatewayTimeout, ErrorResponse{Error: "python worker timeout or unavailable"})
		return
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "failed to read response")
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(respBody)
}

func jsonError(w http.ResponseWriter, code int, msg string) {
	writeJSON(w, code, ErrorResponse{Error: msg})
}

func handleEmbed(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	proxyToPython(w, r, "/api/embed", r.Body)
}

func handleExtract(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	proxyToPython(w, r, "/api/extract", r.Body)
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	workerPool.mu.Lock()
	active := workerPool.active
	cap := workerPool.capacity
	workerPool.mu.Unlock()
	writeJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"workers": fmt.Sprintf("%d/%d", active, cap),
	})
}

func handleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	if err := r.ParseMultipartForm(32 << 20); err != nil {
		jsonError(w, http.StatusBadRequest, "invalid multipart form")
		return
	}
	file, _, err := r.FormFile("image")
	if err != nil {
		jsonError(w, http.StatusBadRequest, "no image file")
		return
	}
	defer file.Close()

	imgData, err := io.ReadAll(file)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "failed to read image")
		return
	}
	b64 := base64.StdEncoding.EncodeToString(imgData)

	alpha := 0.05
	delta := 36.0
	level := 2
	text := r.FormValue("watermark")

	embedReq := EmbedRequest{
		ImageB64:      b64,
		WatermarkText: text,
		Alpha:         alpha,
		Delta:         delta,
		Level:         level,
		SyncEnabled:   true,
		BchEnabled:    true,
	}

	body, err := json.Marshal(embedReq)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "failed to marshal request")
		return
	}
	proxyToPython(w, r, "/api/embed", jsonBody(body))
}

func jsonBody(data []byte) io.Reader {
	r, w := io.Pipe()
	go func() {
		w.Write(data)
		w.Close()
	}()
	return r
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("json encode error: %v", err)
	}
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/embed", corsMiddleware(handleEmbed))
	mux.HandleFunc("/api/extract", corsMiddleware(handleExtract))
	mux.HandleFunc("/api/upload", corsMiddleware(handleUpload))
	mux.HandleFunc("/api/health", corsMiddleware(handleHealth))
	mux.HandleFunc("/", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"service": "s-anchor watermark mediator", "version": "1.0.0"})
	}))

	port := os.Getenv("MEDIATOR_PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("mediator listening on :%s, backend at %s", port, pyHost)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("server error: %v", err)
	}
}

func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next(w, r)
	}
}
