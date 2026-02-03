# Dexter

**Sovereign Evidence Refinery** — ICT forensic extraction. Phoenix "Dream State."

- **Repo:** https://github.com/SlimWojak/Dexter  
- **Location:** `~/dexter/` (Mac Mini MVP) → sovereign M3 Ultra (graduation)  
- **Sibling:** ~/echopeso/phoenix (canonical trading system)  
- **Mascot:** 🔬🧪 | **Motto:** *Mine the ore. Refine the gold. Human decides.*

---

## Setup (stub)

1. **Clone**
   ```bash
   git clone https://github.com/SlimWojak/Dexter.git && cd Dexter
   ```

2. **Env**
   ```bash
   cp .env.example .env
   # Edit .env: set OPENROUTER_KEY, SUPADATA_KEY (see docs/SECURITY.md for credential handling)
   ```

3. **Deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Sandbox (optional)**  
   Run heartbeat in isolation: `./docker-sandbox.sh` (placeholder; Phase 1).

---

**Gate:** Repo clones clean; no secrets; structure matches [architecture](docs/DEXTER_MANIFEST.md).  
*Human frames. Machine computes. Human promotes.*
