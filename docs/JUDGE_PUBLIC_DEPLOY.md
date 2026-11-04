# Judge Public Deployment Guide — InnerOS Meta Guardian

**Project:** InnerOS Autonomous Infrastructure Guardian × Meta Ecosystem  
**Event:** Meta Global AI Developer Hackathon 2026 (Cerebral Valley)  
**Public Live Demo URL:** [https://guardian.pcdoctor.ai/self-heal](https://guardian.pcdoctor.ai/self-heal)  
**Mode:** `PUBLIC_JUDGE_DEMO` (Read-Only Forensic Evidence, 0 Paid Invocations, Isolated Origin)

---

## 1. Architecture Overview

```
                      [ Public Internet / Hackathon Judges ]
                                        │
                                        ▼ HTTPS (TLS 1.3)
                       [ Cloudflare Edge CDN / WAF ]
                         meta-guardian.pcdoctor.ai
                                        │
                         Encrypted Cloudflare Tunnel
                       (Tunnel ID: 6fb8ceab-...-e26ef2d1383f)
                                        │
                                        ▼
                  [ Intel Coordinator Node (192.168.1.4) ]
                   cloudflared opportunityops connector
                                        │
                                        ▼ LAN Forward (Port 8788)
                  [ AMD Primary AI Server (192.168.1.5) ]
                   inneros_meta_guardian.web (daemon service)
                   Environment: GUARDIAN_PUBLIC_MODE=true
```

### Security & Privacy Guarantees
- **Zero Open Router Ports:** No inbound ports on the UniFi router or firewall are opened. All ingress flows outbound via Cloudflare Tunnel.
- **Fail-Closed Public Read-Only Gate:** `POST` mutations, incident injections, live API spending, and orchestrator triggers are strictly rejected with HTTP `403 Forbidden` (`PUBLIC_READ_ONLY_MODE`).
- **No Secret Exfiltration:** All API keys, vault tokens, and internal private IP addresses are sanitized. Zero customer data or camera streams are transmitted.
- **Sovereign Local Inference:** Local Qwen3-Coder-30B-AWQ operates on AMD ROCm 10.1 (Radeon AI PRO R9700) over loopback port 8000.

---

## 2. Ingress & Routing Configuration

- **Cloudflare DNS Route:**
  ```bash
  cloudflared tunnel route dns 6fb8ceab-a17e-41b3-872d-e26ef2d1383f meta-guardian.pcdoctor.ai
  ```
- **Tunnel Ingress Rule (`/home/rlopez/.cloudflared/opportunityops.yml`):**
  ```yaml
  - hostname: meta-guardian.pcdoctor.ai
    service: http://192.168.1.5:8788
  ```
- **Service Management:**
  ```bash
  systemctl --user restart opportunityops-cloudflared.service
  ```

---

## 3. Origin Daemon Configuration on AMD Server (`inneros-5` / `192.168.1.5`)

- **Working Directory:** `/home/rlopez/inneros/inneros-meta-guardian-2026`
- **Systemd Service or Background Process:**
  ```bash
  export PYTHONPATH="/home/rlopez/inneros/inneros-meta-guardian-2026/src"
  export HOST="0.0.0.0"
  export PORT="8788"
  export GUARDIAN_PUBLIC_MODE="true"
  export GUARDIAN_UNSAFE_BIND="true"
  python3 -m inneros_meta_guardian.web
  ```

---

## 4. Verification Checkpoints

1. **DNS Resolution:**
   ```bash
   Resolve-DnsName -Name meta-guardian.pcdoctor.ai
   ```
2. **Health Check:**
   ```bash
   curl -s https://meta-guardian.pcdoctor.ai/api/health
   ```
3. **Public Read-Only Security Gate Check:**
   ```bash
   curl -s -X POST https://meta-guardian.pcdoctor.ai/api/orchestrator/investigate \
     -H "Content-Type: application/json" -d '{"prompt": "test"}'
   # Expects HTTP 403 Forbidden with PUBLIC_READ_ONLY_MODE
   ```
4. **Browser Console Check:**
   Navigate to [https://guardian.pcdoctor.ai/self-heal](https://guardian.pcdoctor.ai/self-heal) to inspect the 5-Panel Investigation Console, Meta Model Lab, and Agent Repair Arena.
