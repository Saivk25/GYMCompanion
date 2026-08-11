/// Shared date/time/duration formatting — the single source for every
/// month/weekday name array and elapsed/duration string this app
/// renders. Previously nine presentation files each defined their own
/// private `_formattedDate`/`_formattedDateTime`/`_formattedTime`/
/// `_formattedDuration`/`_formattedElapsed`, each hardcoding its own
/// literal month-name array for one of a handful of genuinely different
/// output shapes — see `docs/TECH_DEBT.md` TD-0004 for the full history
/// of why consolidation was deliberately deferred until this phase.
///
/// Three real output shapes existed across those copies before this
/// file, plus near-duplicates of each — this file keeps exactly one
/// function per shape, named for what it renders rather than for which
/// screen first needed it, so a tenth caller reaches for one of these
/// instead of writing an eleventh copy.
library;

const List<String> _fullMonths = <String>[
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

const List<String> _shortMonths = <String>[
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

const List<String> _fullWeekdays = <String>[
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

const List<String> _shortWeekdays = <String>[
  'Mon',
  'Tue',
  'Wed',
  'Thu',
  'Fri',
  'Sat',
  'Sun',
];

/// "Monday, January 5" — full weekday + full month + day, no year.
/// Today's own page header (`TodayScreen`), where the date is always
/// today or very recent and the year would be redundant noise.
String appWeekdayMonthDay(DateTime date) {
  return '${_fullWeekdays[date.weekday - 1]}, ${_fullMonths[date.month - 1]} ${date.day}';
}

/// "January 5, 2026" — full month, day, and year. Used where the date
/// could plausibly be far enough in the past that the year matters
/// (`ReadinessEntryDetailScreen`, `SessionSummaryScreen`).
String appMonthDayYear(DateTime date) {
  return '${_fullMonths[date.month - 1]} ${date.day}, ${date.year}';
}

/// "Jan 5" — short month + day, no year. Dense list rows where the
/// current year is implied (`ReadinessEntryTile`, `TrainHistoryTile`).
String appShortMonthDay(DateTime date) {
  return '${_shortMonths[date.month - 1]} ${date.day}';
}

/// "Today" / "Tomorrow" / "Mon" (short weekday) — relative to today,
/// for near-future planning surfaces (`TrainWorkoutCard`,
/// `PreSessionScreen`). [now] is exposed only for deterministic tests;
/// real call sites should omit it and let it default.
String appRelativeDay(DateTime date, {DateTime? now}) {
  final DateTime today = _dateOnly(now ?? DateTime.now());
  final DateTime target = _dateOnly(date);
  final int diff = target.difference(today).inDays;
  if (diff == 0) return 'Today';
  if (diff == 1) return 'Tomorrow';
  return _shortWeekdays[date.weekday - 1];
}

DateTime _dateOnly(DateTime dateTime) {
  return DateTime(dateTime.year, dateTime.month, dateTime.day);
}

/// "3:45 PM" — 12-hour clock, time only, no date (`MealEntryTile`).
String appTimeOfDay(DateTime time) {
  final int hour12 = time.hour % 12 == 0 ? 12 : time.hour % 12;
  final String minute = time.minute.toString().padLeft(2, '0');
  final String period = time.hour >= 12 ? 'PM' : 'AM';
  return '$hour12:$minute $period';
}

/// "January 5 at 3:45 PM" — full month + day, combined with clock time
/// (`CoachSignalDetailScreen`, disclosing exactly when a rule fired).
String appMonthDayAtTime(DateTime dateTime) {
  return '${_fullMonths[dateTime.month - 1]} ${dateTime.day} at ${appTimeOfDay(dateTime)}';
}

/// "45 min" — a completed workout session's total duration, rounded to
/// the nearest minute from a real elapsed-seconds value
/// (`SessionSummaryScreen`).
String appDurationMinutes(double seconds) {
  final int minutes = (seconds / 60).round();
  return '$minutes min';
}

/// "12:34" — a live, in-progress elapsed-time display
/// (`ActiveWorkoutScreen`'s running session clock). Unlike
/// [appDurationMinutes], this is a ticking mm:ss stopwatch reading off a
/// [Duration], not a rounded total computed once at the end.
String appElapsedTime(Duration elapsed) {
  final int minutes = elapsed.inMinutes;
  final int seconds = elapsed.inSeconds % 60;
  return '$minutes:${seconds.toString().padLeft(2, '0')}';
}
