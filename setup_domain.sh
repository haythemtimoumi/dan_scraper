#!/bin/bash

# Setup script for stock-ticker.dev domain
echo "Setting up stock-ticker.dev domain..."

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Install flask-cors if not already installed
echo "Installing flask-cors..."
pip3 install flask-cors

# Stop nginx temporarily
systemctl stop nginx

# Get SSL certificate
echo "Obtaining SSL certificate for stock-ticker.dev..."
certbot certonly --standalone -d stock-ticker.dev -d www.stock-ticker.dev --non-interactive --agree-tos --email admin@stock-ticker.dev

# Copy nginx configuration
echo "Updating nginx configuration..."
cp /root/dan_scraper/nginx.conf /etc/nginx/sites-available/stock-ticker.dev
ln -sf /etc/nginx/sites-available/stock-ticker.dev /etc/nginx/sites-enabled/

# Remove default nginx site if it exists
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid"
    systemctl start nginx
    systemctl enable nginx
    echo "Nginx started and enabled"
else
    echo "Nginx configuration error!"
    exit 1
fi

# Setup auto-renewal for SSL certificates
echo "Setting up SSL certificate auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

echo "Domain setup complete!"
echo "Your API is now available at:"
echo "- https://stock-ticker.dev"
echo "- https://www.stock-ticker.dev"