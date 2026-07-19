package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestTokenBucket_allow(t *testing.T) {
	tb := newTokenBucket(3, 50*time.Millisecond)
	for i := range 3 {
		if !tb.allow() {
			t.Fatalf("expected allow at request %d", i)
		}
	}
	if tb.allow() {
		t.Fatal("expected deny after burst exhausted")
	}
	time.Sleep(60 * time.Millisecond)
	if !tb.allow() {
		t.Fatal("expected allow after refill")
	}
}

func TestWorkerPool_acquireRelease(t *testing.T) {
	p := NewWorkerPool(2)
	p.Acquire()
	p.Acquire()
	done := make(chan bool)
	go func() {
		p.Acquire()
		done <- true
	}()
	select {
	case <-done:
		t.Fatal("acquire should block when full")
	case <-time.After(10 * time.Millisecond):
	}
	p.Release()
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("acquire should unblock after release")
	}
	p.Release()
}

func TestCORS_allowedOrigin(t *testing.T) {
	handler := corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Origin", "http://127.0.0.1:8000")
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.Header.Get("Access-Control-Allow-Origin") != "http://127.0.0.1:8000" {
		t.Fatal("expected CORS for allowed origin")
	}
}

func TestCORS_deniedOrigin(t *testing.T) {
	handler := corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Origin", "https://evil.com")
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.Header.Get("Access-Control-Allow-Origin") == "https://evil.com" {
		t.Fatal("should deny CORS for unknown origin")
	}
}

func TestCORS_preflight(t *testing.T) {
	handler := corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		t.Fatal("preflight should not reach handler")
	})
	req := httptest.NewRequest(http.MethodOptions, "/api/embed", nil)
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", resp.StatusCode)
	}
}

func TestRateLimitHTTP(t *testing.T) {
	oldRL := rateLimiter
	rateLimiter = newTokenBucket(3, time.Hour)
	defer func() { rateLimiter = oldRL }()
	body := `{"image_b64":"dGVzdA==","watermarks":[]}`
	handler := corsMiddleware(handleEmbed)
	for range 3 {
		req := httptest.NewRequest(http.MethodPost, "/api/embed", strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		handler(w, req)
	}
	req := httptest.NewRequest(http.MethodPost, "/api/embed", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusTooManyRequests {
		t.Fatalf("expected 429, got %d", resp.StatusCode)
	}
}

func TestHealthEndpoint(t *testing.T) {
	handler := corsMiddleware(handleHealth)
	req := httptest.NewRequest(http.MethodGet, "/api/health", nil)
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	var body map[string]string
	json.NewDecoder(resp.Body).Decode(&body)
	if body["status"] != "ok" {
		t.Fatal("expected status ok")
	}
}

func TestWatermarkTypesEndpoint(t *testing.T) {
	handler := corsMiddleware(handleWatermarkTypes)
	req := httptest.NewRequest(http.MethodGet, "/api/watermark-types", http.NoBody)
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusGatewayTimeout && resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 504 (no backend) or 200, got %d", resp.StatusCode)
	}
}

func TestEmbedEndpoint_noImage(t *testing.T) {
	handler := corsMiddleware(handleEmbed)
	body := `{"image_b64":"bad","watermarks":[]}`
	req := httptest.NewRequest(http.MethodPost, "/api/embed", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode == http.StatusOK {
		t.Fatal("expected non-200 for invalid image")
	}
}

func TestMethodNotAllowed(t *testing.T) {
	handler := corsMiddleware(handleEmbed)
	req := httptest.NewRequest(http.MethodGet, "/api/embed", nil)
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("expected 405, got %d", resp.StatusCode)
	}
}

func TestRootEndpoint(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"service": "s-anchor watermark mediator", "version": "1.0.0"})
	}))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
}

func TestUploadEndpoint_noFile(t *testing.T) {
	handler := corsMiddleware(handleUpload)
	req := httptest.NewRequest(http.MethodPost, "/api/upload", nil)
	req.Header.Set("Content-Type", "multipart/form-data; boundary=test")
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", resp.StatusCode)
	}
}

func TestCapacityEndpoint(t *testing.T) {
	handler := corsMiddleware(handleCapacity)
	req := httptest.NewRequest(http.MethodGet, "/api/capacity?width=256&height=256&level=2&sync_enabled=true&bch_enabled=true", nil)
	w := httptest.NewRecorder()
	handler(w, req)
	resp := w.Result()
	if resp.StatusCode != http.StatusGatewayTimeout && resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 504 (no backend) or 200, got %d", resp.StatusCode)
	}
}
