services:
  redis:
    image: redis:7.2.4-alpine  
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 1s
      timeout: 3s
      retries: 30
      
  frontend:
    build:
      context: ..
      dockerfile: Dockerfile
    ports:
      - "8080:8080"   # Puerto HTTP (redirect a HTTPS)
      - "8443:8443"   # Puerto HTTPS
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    healthcheck:
      test: ["CMD", "curl", "-k", "http://localhost:8080/actuator/health"]  # Verifica la salud del servicio
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

volumes:
  redis-data:  
  ollama-models: