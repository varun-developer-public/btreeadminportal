# Deployment Notes

## Nginx Configuration for File Uploads

When deploying this application, ensure that Nginx is configured to allow sufficient file upload sizes. The default Nginx limit is often 1MB, which is too small for offer letters and other documents.

### Error Symptom
If you see `413 Content Too Large` (Request Entity Too Large), it means the uploaded file exceeds the Nginx `client_max_body_size` limit.

### Fix
Edit your Nginx configuration file (usually located at `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/btreeadminportal` on the server).

Add or update the `client_max_body_size` directive in the `http`, `server`, or `location` block:

```nginx
server {
    ...
    client_max_body_size 20M;
    ...
}
```

After changing the configuration, restart Nginx:

```bash
sudo systemctl restart nginx
```

## Django Settings

Ensure `DATA_UPLOAD_MAX_MEMORY_SIZE` in `core/settings.py` is sufficient if you are handling large non-file payloads, though for standard file uploads via `FileField`, Django streams them to disk so memory limits are less critical.

server { 
     server_name btrees.in www.btrees.in; 
     
     # ADD THIS LINE HERE
     client_max_body_size 50M;

     location = /favicon.ico { access_log off; log_not_found off; } 
     location /static/ { 
         root /var/www/btreeadminportal; 
     } 
     # ... rest of your config
}