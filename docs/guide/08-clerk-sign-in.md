# Signing in with Clerk

The dashboard can sign people in two ways. Which one is in use is a server
setting; a reader does not choose.

> **Right now the deployed version uses the local sign-in.** Clerk sign-in is
> available for development only, and will be replaced by Georgia Tech
> single sign-on once the project is provisioned. If you were sent here to set up
> a Clerk account, you do not need one — you will be asked for the shared
> passcode, then to pick your name.

## The two ways

- **Local (the stopgap).** A shared passcode, then you pick your name.
- **Clerk (the identity provider).** You sign in with Clerk, and the dashboard
  verifies your session and matches you to your name in its own directory.

Either way, **what you may do is decided by the dashboard's own roles**, not by
the sign-in method. Clerk answers "who are you"; the dashboard answers "what may
you do".

## If you sign in with Clerk

1. Open the dashboard; you are sent to the Clerk sign-in page.
2. Sign in or sign up. Clerk may email you a code.
3. **The first time**, your account is not yet linked to your name, so you will
   see a page saying so. An administrator links your Clerk account to your person
   in the dashboard's directory, once. After that you go straight in.
4. To sign out, open your name in the top-right menu and choose **Sign out**.

## If you are an administrator

- Linking a person to Clerk is a one-time step per person: set their Clerk user
  id on their People row. Until it is set, they can sign in but see the "not
  linked" page — never someone else's data.
- The Clerk publishable key and secret key are server settings. The secret key
  must never be placed in a page or a script; the dashboard only ever sends the
  publishable key to the browser.

## Why it is built this way

The sign-in method is a swappable adapter behind one seam, so the dashboard is
not tied to any one provider. This is recorded as ADR-0004 in the repository.
