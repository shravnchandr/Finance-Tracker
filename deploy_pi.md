# Deploying Finance Tracker on Raspberry Pi

This guide will help you set up the Finance Tracker on a Raspberry Pi and make it accessible from the internet using Cloudflare Tunnel.

## Prerequisites

- Raspberry Pi (3, 4, or 5 recommended) with Raspberry Pi OS installed.
- Internet connection.
- Terminal access (SSH or direct).

## 1. Clone the Repository

Open a terminal on your Pi and run:

```bash
cd /home/pi
git clone <your-repo-url> finance-tracker
cd finance-tracker
```

## 2. Set Up Virtual Environment

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

Install the required Python packages, including Gunicorn:

```bash
pip install -r requirements.txt
```

## 4. Configure Systemd Service

We will use `systemd` to keep the app running in the background and restart it automatically.

1.  **Edit the service file** (if needed):
    Check `finance-tracker.service`. If your user is not `pi` or you installed it somewhere else, update the `User`, `Group`, `WorkingDirectory`, and `ExecStart` paths.
    
    **Important:** Change the `FLASK_SECRET_KEY` in the service file to a secure random string!

2.  **Copy the service file**:
    ```bash
    sudo cp finance-tracker.service /etc/systemd/system/
    ```

3.  **Start and Enable the service**:
    ```bash
    sudo systemctl start finance-tracker
    sudo systemctl enable finance-tracker
    ```

4.  **Check status**:
    ```bash
    sudo systemctl status finance-tracker
    ```
    You should see "Active: active (running)".

At this point, your app is running on your local network at `http://<your-pi-ip>:8000`.

---

## 5. Expose to the Internet (Cloudflare Tunnel)

To access your app from anywhere securely (without port forwarding), use Cloudflare Tunnel.

### Step A: Install `cloudflared`

Run the following commands on your Pi:

```bash
# Add Cloudflare GPG key
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add Cloudflare repo
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Update and install
sudo apt-get update && sudo apt-get install cloudflared
```
*(Note: If `jammy` doesn't work for your OS version, check [Cloudflare docs](https://pkg.cloudflare.com/index.html) for the correct codename, e.g., `bullseye` or `bookworm`)*.

### Step B: Authenticate

```bash
cloudflared tunnel login
```
This will print a URL. Visit it in your browser to authorize your domain.

### Step C: Create a Tunnel

```bash
cloudflared tunnel create finance-tracker
```
Copy the **Tunnel ID** from the output.

### Step D: Configure DNS

Route a domain (e.g., `finance.yourdomain.com`) to your tunnel:

```bash
cloudflared tunnel route dns finance-tracker finance.yourdomain.com
```

### Step E: Run the Tunnel

Create a config file `~/.cloudflared/config.yml`:

```yaml
tunnel: <Your-Tunnel-ID>
credentials-file: /home/pi/.cloudflared/<Your-Tunnel-ID>.json

ingress:
  - hostname: finance.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

Run the tunnel:
```bash
cloudflared tunnel run finance-tracker
```

### Step F: Run Tunnel as a Service

To keep the tunnel running after reboot:

```bash
sudo cloudflared service install
sudo systemctl start cloudflared
```

Now your app is accessible at `https://finance.yourdomain.com`!
