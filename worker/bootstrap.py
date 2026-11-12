# Private Kaggle kernel entry point. Holds nothing private: it fetches the real worker from the owner's private repo
# with the token stored in this kernel's Kaggle Secrets (SF_GH_TOKEN) and runs it.
import urllib.request

from kaggle_secrets import UserSecretsClient

tok = UserSecretsClient().get_secret("SF_GH_TOKEN")
req = urllib.request.Request(
    "https://api.github.com/repos/D0ND1/signalforge-os/contents/deploy/kaggle/worker.py",
    headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.raw"},
)
code = urllib.request.urlopen(req, timeout=60).read().decode()
exec(compile(code, "worker.py", "exec"), {"__name__": "__main__"})
