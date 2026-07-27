import os

# Defaults assume this server runs inside the lab-environment docker-compose
# network, reaching each backend by service name (see that repo's
# docker-compose.yml). Override via env vars when running standalone.
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
JAEGER_URL = os.environ.get("JAEGER_URL", "http://jaeger:16686")
CONSUL_URL = os.environ.get("CONSUL_URL", "http://consul:8500")

HTTP_TIMEOUT_SECONDS = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "10"))
