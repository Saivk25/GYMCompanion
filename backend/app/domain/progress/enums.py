"""Closed-set categorical values used by the Progress aggregate.

Neither enum is drawn verbatim from a Domain Model & Decision Engine Bible
table the way, say, `app.domain.user.enums.AccountStatus` is — the Bible's
closest concept, `Measurement` (Section 4.10, Table 13), carries a free-text
`method_note` rather than a structured unit or provenance field. Both enums
here are this increment's own addition: a raw measurement number is not
meaningful without knowing its unit, and "how was this value obtained"
(typed by hand vs. synced from a device vs. derived from other fields) is
exactly the kind of provenance future Progress Intelligence work (trend
computation, plateau detection — neither built yet) will need to weigh
manual entries differently from device-sourced ones.

Both inherit `str` as well as `Enum` so a member serializes to exactly its
`.value` wherever it's written to JSON, a database column, or an event
payload — the same convention every other enum in this codebase follows.
"""

from enum import Enum


class MeasurementUnit(str, Enum):
    """The unit system every numeric value on one `Progress` record is
    expressed in. One unit per record, not per field — recording a single
    check-in with, say, weight in kilograms and waist in inches would be a
    data-entry mistake, not a legitimate mixed-unit record, so `Progress`
    carries exactly one `MeasurementUnit` rather than tagging each
    measurement independently.
    """

    METRIC = "metric"
    IMPERIAL = "imperial"


class ProgressSource(str, Enum):
    """Where a `Progress` record's values came from. `CALCULATED` covers a
    value derived from other recorded data (e.g. a lean body mass computed
    from weight and body fat percentage) rather than directly measured or
    entered — this aggregate stores the number either way; performing that
    calculation is explicitly out of scope here (see the module docstring
    in `progress.py`).
    """

    MANUAL = "manual"
    SMART_SCALE = "smart_scale"
    CALCULATED = "calculated"
