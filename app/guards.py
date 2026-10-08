"""Request guards: resolve the caller, the target, and permission once.

Design D2 of deepen-dashboard-modules. A route declares what it needs; the
guard decides, in one place, whether the request may proceed and with what. The
rules it enforces are the `request-guards` spec:

* existence before permission - an unknown or retired code is 404, never 403;
* permission is decided on the server, so hiding a control is not the control;
* the caller's person is resolved once per request (auth.current_person caches).

Routes declare a guard with `Depends(...)` and receive a resolved record, rather
than each repeating the same three clauses.
"""

from dataclasses import dataclass

from fastapi import HTTPException, Request

from app import auth, queries


@dataclass(frozen=True)
class Target:
    """A resolved request: who is asking, what they are asking about, and may they.

    `card` is the initiative card (or None for a route with no target); `person`
    is the signed-in person, guaranteed present because the guard runs behind
    the access gate.
    """
    person: dict
    card: dict | None = None

    @property
    def person_id(self) -> int:
        return self.person["PersonID"]

    @property
    def card_id(self) -> int:
        """The resolved card's id, for the routes that always carry a card.

        `card` is `dict | None` because `admin_only` routes have no target, but
        `admin_for` (tags, links, retire) ALWAYS resolves one. Reaching into
        `card["InitiativeID"]` at those routes read as "this might be None" -
        the type is right, the use site is what needed the invariant stated.
        Asking a card-less target for its id is a wiring mistake, so this fails
        loudly rather than raising a bare TypeError.
        """
        assert self.card is not None, "this route has no target card"
        return self.card["InitiativeID"]


def _person_or_500(request: Request) -> dict:
    """The signed-in person, or a hard error if the gate let a request through.

    Every guarded route sits behind the access gate, so a missing person here is
    a wiring mistake, not a user state. Answering 500 makes it visible rather
    than silently treating the caller as unauthenticated.
    """
    person = auth.current_person(request)
    if person is None:
        raise HTTPException(status_code=500, detail="No signed-in person behind the gate")
    return person


def _resolve_target(request: Request, mi_id: str, check) -> Target:
    # Existence BEFORE permission (the spec's ordering rule). The card read also
    # supplies the row the permission check and the handler need, so the target
    # is read once.
    card = queries.initiative_card(mi_id)
    if card is None:
        raise HTTPException(status_code=404, detail="No such initiative")
    person = _person_or_500(request)
    if not check(person, card):
        raise HTTPException(status_code=403, detail="You cannot act on this initiative")
    return Target(person=person, card=card)


def may_update(request: Request, mi_id: str) -> Target:
    """Owner, Operator (Strategic Operations), or Administrator may append a
    progress update. NOT the Executive Sponsor by virtue of being Dean (DR-23):
    the Dean authorizes a change through an executive action; Strategic
    Operations performs the routine data update."""
    def check(person, card):
        return (auth.is_admin(person) or auth.is_operator(person)
                or card["OwnerID"] == person["PersonID"])

    return _resolve_target(request, mi_id, check)


def may_edit_details(request: Request, mi_id: str) -> Target:
    """Owner or admin may edit an initiative's name and description."""
    def check(person, card):
        return (auth.is_admin(person) or card["OwnerID"] == person["PersonID"])

    return _resolve_target(request, mi_id, check)


def admin_only(request: Request) -> Target:
    """A route only an admin may reach. No target code."""
    person = _person_or_500(request)
    if not auth.is_admin(person):
        raise HTTPException(status_code=403, detail="Admins only")
    return Target(person=person)


def admin_for(request: Request, mi_id: str) -> Target:
    """An admin-only route that names an initiative (tags, links, retire)."""
    def check(person, card):
        return auth.is_admin(person)

    return _resolve_target(request, mi_id, check)


def known_target(request: Request, mi_id: str) -> Target:
    """A route that needs the initiative to exist but sets no permission floor.

    Used by the card view and the update form's existence check; permission for
    editing is still enforced by the write routes below.
    """
    card = queries.initiative_card(mi_id)
    if card is None:
        raise HTTPException(status_code=404, detail="No such initiative")
    return Target(person=_person_or_500(request), card=card)
