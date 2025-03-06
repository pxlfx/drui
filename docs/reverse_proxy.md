# Reverse Proxy Configuration

To deploy DRUI in a production environment, it is recommended to use a reverse
proxy. A reverse proxy can handle SSL termination, load balancing, and other
advanced features. Below are instructions for setting up a reverse proxy using
**Nginx** and **Apache**.

---

## Using Nginx as a Reverse Proxy

Add the following parameters for your Nginx configuration:

```nginx
server {
   listen 80;
   server_name your-domain.io;

   location / {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-Prefix /reg/
   }
}
```

> [!NOTE]
> * replace `server_name your-domain.io` with your actual domain name
> * replace `proxy_pass http://127.0.0.1:8000` with your actual DRUI address
> * replace ` proxy_set_header X-Forwarded-Prefix /reg/` with your actual DRUI
>   site prefix

## Using Apache as a Reverse Proxy

Add the following parameters for your Apache configuration:

   ```apache
   <VirtualHost *:80>
       ServerName your-domain.io

       ProxyPreserveHost On
       ProxyPass / http://127.0.0.1:8000/
       ProxyPassReverse / http://127.0.0.1:8000/
       RequestHeader set X-Forwarded-Prefix /reg/
   </VirtualHost>
   ```

> [!NOTE]
> * replace `server_name your-domain.io` with your actual domain name
> * replace `ProxyPass / http://127.0.0.1:8000/` with your actual DRUI address
> * replace `ProxyPassReverse / http://127.0.0.1:8000/` with your actual DRUI
>   address
> * replace `RequestHeader set X-Forwarded-Prefix /reg/` with your actual DRUI
>   site prefix

## Next Steps

- Visit the [GitHub repository](https://github.com/pxlfx/drui) for more
  information, issues, and contributions.
