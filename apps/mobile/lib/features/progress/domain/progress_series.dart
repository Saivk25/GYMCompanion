import 'progress_models.dart';

/// Pure data-shaping helpers for turning real [ProgressEntry] lists into
/// the value/label arrays `AppLineChart` renders. Kept out of any
/// widget's `build()` per this project's "no business logic inside
/// widgets" rule — this is presentation-adjacent shaping, not a domain
/// rule in the Rule Engine sense, but it is still real arithmetic over
/// real data that deserves to live somewhere unit-testable and reusable
/// rather than inlined once per screen.
library;

/// A simple trailing rolling average — the mean of up to [window] values
/// ending at each index (fewer, if fewer exist yet). Mirrors the Bible's
/// own "Measurements" chart rule (Section 12): "a rolling-average line
/// as the primary series... raw points are context only." A `null` entry
/// in [values] (nothing recorded that point) is excluded from its
/// window's average rather than treated as zero.
List<double?> rollingAverage(List<double?> values, {int window = 3}) {
  final List<double?> result = <double?>[];
  for (int i = 0; i < values.length; i++) {
    final int start = (i - window + 1).clamp(0, values.length);
    final List<double> slice =
        values.sublist(start, i + 1).whereType<double>().toList();
    result.add(
      slice.isEmpty
          ? null
          : slice.reduce((double a, double b) => a + b) / slice.length,
    );
  }
  return result;
}

/// Extracts [metric]'s value from each of [entriesOldestFirst], in
/// order — the raw series [rollingAverage] is computed from, and the
/// same series a chart's `rawValues` plots underneath it.
List<double?> extractMetricSeries(
  List<ProgressEntry> entriesOldestFirst,
  MeasurementMetric metric,
) {
  return entriesOldestFirst.map(metric.valueFrom).toList();
}
