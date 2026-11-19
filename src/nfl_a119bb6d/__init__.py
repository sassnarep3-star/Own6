"""Session a119bb6d — official NFL Game Books, availability graph, snapshot automation.

The pack answers the requirement that earlier packs had to mark *blocked* because
no official source of actual starters, game-day status, playing time, venue or
weather could be found.

What changed the answer: the NFL publishes an **official Game Book** for every
completed game, linked from the league's own game centre page
(``https://www.nfl.com/games/<slug>`` -> "Download Game Book (PDF)"). The game
book carries, in the league's own words and format:

* the official starting eleven on offense and defense for both clubs,
* the *Not Active* list (the game-day inactive list),
* the stadium and the city,
* the 90-minute roof / surface designation,
* the game-day weather (sky, temperature, humidity, wind),
* the final score by quarter and the paid attendance.

Every number this pack publishes is copied from that document or from an
official league page, and every row carries the URL it came from. Nothing is
inferred: where the source does not print a value, the cell is blank and the
row is flagged as unverified.

Rights note (this is a live question, not a settled one): the game book PDF
carries the league's own copyright statement, quoted in
``data/nfl_a119bb6d/terms_note.md``. This pack does not redistribute the PDFs.
It records their SHA-256 and the URL so any reviewer can re-download and confirm
the hash, and it commits only short verbatim extracts with citations.
"""
