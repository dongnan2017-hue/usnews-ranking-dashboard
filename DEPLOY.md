# Deploying this dashboard

The app is self-contained: `app.py` plus the files in `data/`. It holds only published
U.S. News ranking data and IPEDS sector classification. There are no credentials, API
keys or secrets of any kind.

## Option 1 - Docker, on any internal server

```
docker build -t usnews-dashboard .
docker run -p 8501:8501 usnews-dashboard
```

## Option 2 - Azure App Service (single sign-on)

Right choice if you want the app inside institutional infrastructure with Entra ID
authentication, so viewers sign in with their existing account.

```powershell
az webapp up --name usnews-dashboard --runtime "PYTHON:3.12" --sku B1
az webapp config set --name usnews-dashboard --resource-group <rg> `
  --startup-file "streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
```

Then enable **Authentication -> Microsoft Entra ID** and require authentication.

## Option 3 - Local, or shared on the LAN

`.streamlit/config.toml` binds to `127.0.0.1`, so by default only your machine can reach
it:

```
streamlit run app.py
```

To let colleagues on the network reach it:

```
streamlit run app.py --server.address 0.0.0.0
```

It prints a Network URL such as `http://192.168.1.182:8501`. Anyone on the network can
open that with **no authentication**. The process stops when the terminal closes; wrap it
with [NSSM](https://nssm.cc/) to run it as a Windows service.

## A note on Streamlit Community Cloud

Community Cloud deploys **public** apps only on the free tier, and reading a private
repository requires granting Streamlit the GitHub `repo` scope - read/write access to
every repository on the account, since GitHub cannot scope an OAuth grant to one repo.
Private hosting has moved to Snowflake on a paid plan. If the repository must stay
private, use Option 1 or 2 instead.

## After the September 2026 release

1. Download refreshed Reiter workbooks into `data/`.
2. Rebuild `data/rankings.json` from them.
3. Bump `LATEST_PUBLIC` to 2027 in `app.py`.
