#!/bin/bash

# Copy all service files to systemd directory
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable month-rule.service
sudo systemctl enable stockscores-to-db.service
sudo systemctl enable rule1-guru-to-db.service
sudo systemctl enable dan-watchlist-to-db.service
sudo systemctl enable rule1-list-to-db.service
sudo systemctl enable run-sequential-scraping.service
sudo systemctl enable main-scraper.service

# Enable and start timer
sudo systemctl enable main-scraper.timer
sudo systemctl start main-scraper.timer

echo "All services installed and main timer started"