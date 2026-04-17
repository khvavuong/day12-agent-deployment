# Deployment Information

## Public URL

`https://day12-agent-deployment-7ad0.onrender.com`

## Platform

Render

## Test Commands

### Health Check

```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)

```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_PROD_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

## Environment Variables Set

![alt text](../screenshots/env_variable.png)

## Screenshots

### Deployment dashboard

![Deployment dashboard](../screenshots/dashboard.png)

### Service running

![Service running](../screenshots/running.png)

### Test results

![Test results](../screenshots/test.png)

#### Check health

![alt text](../screenshots/health.png)

#### Check chat

![alt text](../screenshots/check_chat.png)

### Images size

```bash
health_care-agent:latest                                                                 f898b6d46e37        191MB             0B    U
```
