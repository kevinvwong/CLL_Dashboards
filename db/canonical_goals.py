"""The five canonical Strategy 2035 goals.

GENERATED from the canonical deck, not typed. Source:
  CLL-strategy-2035-presentation.pptx, slide 7, "College Goals: How We Will
  Advance Our Vision"

That deck is the authority both the enterprise package and the wireframes
name. The package matches this wording word for word; the prototype's seed
did not - goals 3 and 4 were transposed and goals 2-5 had no title. Fixing it
meant re-seeding from here, not editing rows: a goal's number is its identity,
and editing a number moves the initiatives tagged to it.

Regenerate with scripts/extract_canonical_goals.py if the deck changes.
"""

SOURCE = "CLL-strategy-2035-presentation.pptx, slide 7"

VISION = 'To be the catalyst for limitless learning that transforms lives through access, innovation, and relevance.'

# number, short label, canonical title
GOALS = [
    (1, 'Academic', 'Catalyze a learning society and build the world’s home for transformative learning systems leaders.'),
    (2, 'Extension', 'Empower communities with limitless learning and scale our extension model for global impact.'),
    (3, 'Learner', 'Engage 5 million learners with Georgia Tech–designed lifetime learning touchpoints.'),
    (4, 'Research', 'Be the global thought leader in optimized learning systems.'),
    (5, 'Operational', 'Revolutionize an operational model that is seamless, data-rich, proactive, and delivers a learner-first experience.'),
]
