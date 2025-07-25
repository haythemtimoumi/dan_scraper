#!/bin/bash

# Setup API Service Script
echo "🔧 Setting up API service..."

# Create systemd service file
sudo tee /etc/systemd/system/scraper-api.service > /dev/null <<EOF
[Unit]
Description=Stock Scraper API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/dan_scraper/api
ExecStart=/usr/bin/python3 /root/dan_scraper/api/server.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/root/dan_scraper

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable scraper-api.service
sudo systemctl start scraper-api.service

echo "✅ Service setup complete!"
echo "📡 API running at http://localhost:5000"
echo ""
echo "Service commands:"
echo "  sudo systemctl status scraper-api    # Check status"
echo "  sudo systemctl stop scraper-api      # Stop service"
echo "  sudo systemctl start scraper-api     # Start service"
echo "  sudo systemctl restart scraper-api   # Restart service"