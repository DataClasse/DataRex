# utils/monitoring.py
from prometheus_client import Counter, Histogram, make_asgi_app

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency')
def setup_metrics(app):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    @app.middleware("http")
    async def monitor_requests(request, call_next):
        start_time = time.time()
        REQUEST_COUNT.inc()
        response = await call_next(request)
        latency = time.time() - start_time
        REQUEST_LATENCY.observe(latency)
        return response