"""Add a verified secondary email (an alias) to a Clerk user.

    python scripts/add_clerk_email.py <clerk_user_id> <email>

A GT person often has two addresses for the same account — a username form
(<username>@gatech.edu) and an alias (first.last@lifetimelearning.gatech.edu).
Microsoft SSO returns ONE of them; Clerk auto-links an SSO sign-in only when the
returned address matches a VERIFIED email already on the user. So each person
should carry BOTH addresses, both verified. This adds the second one.

Idempotent: if the email is already on the user, it says so and does nothing.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLERK = os.environ.get("CLERK_NODE", r"C:\Users\kwong318\scoop\apps\nodejs-lts\current\node.exe")
JS = os.environ.get(
    "CLERK_JS",
    r"C:\Users\kwong318\scoop\persist\nodejs-lts\bin\node_modules\clerk\bin\clerk")
APP = os.environ.get("CLERK_APP_ID", "app_3KPot74L7qbEcADeZzaSQerlWfg")


def _clerk(args, body=None):
    cmd = [CLERK, JS] + args + ["--app", APP]
    if body is not None:
        path = os.path.join(os.environ.get("TEMP", "/tmp"), "_clerk_body.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
        cmd += ["--method", "POST", "--file", path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.stdout, p.stderr


def add_email(user_id, email):
    out, err = _clerk(["/email_addresses"], body={"user_id": user_id, "email_address": email})
    try:
        data = json.loads(out)
    except Exception:
        # Already present, or an error.
        print("could not add %s: %s" % (email, (err or out)[:160]))
        return 1
    if data.get("errors"):
        msg = data["errors"][0].get("message", "")
        print("%s not added: %s" % (email, msg))
        return 0 if "exists" in msg.lower() else 1
    eid = data.get("id")
    out2, err2 = _clerk(["/email_addresses/%s" % eid], body={"verified": True})
    try:
        v = json.loads(out2).get("verification", {}).get("status")
    except Exception:
        v = "?"
    print("%s -> %s (%s)" % (email, eid, v))
    return 0 if v == "verified" else 1


def main(argv=None):
    args = (argv if argv is not None else sys.argv)[1:]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    return add_email(args[0], args[1])


if __name__ == "__main__":
    raise SystemExit(main())
