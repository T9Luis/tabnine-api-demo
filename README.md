# Tabnine API Demo

An interactive Streamlit application that lets you explore and run every endpoint of the [Tabnine Team Management API](https://docs.tabnine.com/main/administering-tabnine/managing-your-team/tabnine-apis) directly from your browser — no local setup required for your colleagues.

---

## Live Demo

> Deploy steps below take ~2 minutes. Once done, paste your `https://<your-app>.streamlit.app` URL here and commit it so colleagues land straight on it.
>
> GitHub repo: **https://github.com/T9Luis/tabnine-api-demo**

---

## What it covers

The demo exposes all documented Tabnine API capabilities through a point-and-click interface:

| Capability | Method | Description |
|---|---|---|
| List Users | GET | All users in your team |
| Get User | GET | Single user by email |
| Add User | POST | Add & seat a new user |
| Remove User | DELETE | Remove a user & release seat |
| List Groups | GET | All groups in your org |
| Get Group | GET | Single group by name |
| Create Group | POST | Create a new group |
| Delete Group | DELETE | Delete an existing group |
| Add User to Group | POST | Assign a user to a group |
| Remove User from Group | DELETE | Remove a user from a group |
| Usage Report | GET | Team-wide usage statistics |

For each call the app shows the live API response, an HTTP status badge, and a ready-to-copy `curl` equivalent.

---

## Deploy to Streamlit Community Cloud (recommended — free, hosted on GitHub)

This is the fastest way to give colleagues a shareable URL with zero infrastructure.

**Step 1 — The repo is already on GitHub.**

The repository lives at `https://github.com/T9Luis/tabnine-api-demo`. Any future changes you push will automatically redeploy the app.

**Step 2 — Create a free Streamlit Cloud account.**

Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

**Step 3 — Deploy the app.**

Click **New app**, select your repository and branch, set **Main file path** to `app.py`, and click **Deploy**. Streamlit Cloud will install dependencies automatically from `requirements.txt`.

**Step 4 — Share the URL.**

Streamlit Cloud gives you a public URL in the format `https://<your-app>.streamlit.app`. Share that with your colleagues — they only need to paste an API token to start exploring.

Every `git push` to `main` automatically redeploys the app.

---

## Run locally

If you want to run the demo on your own machine first:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Security notes

- The API token is entered at runtime via a password-masked field and is never written to disk, logged, or sent anywhere except the Tabnine API.
- Never commit a real token to this repository.
- Destructive operations (DELETE, and group/user removals) require an explicit confirmation checkbox before the call is made.

---

## References

- [Tabnine API documentation](https://docs.tabnine.com/main/administering-tabnine/managing-your-team/tabnine-apis)
- [Tabnine Admin Console](https://app.tabnine.com)
- [Streamlit Community Cloud](https://share.streamlit.io)
