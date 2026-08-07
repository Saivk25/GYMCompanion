import 'package:flutter/material.dart';

import '../theme/app_semantic_colors.dart';
import '../tokens/tokens.dart';

/// A restrained line chart — this app's one line-chart component, built
/// for Progress's real trend surfaces (Section 12: "Consistent axis and
/// legend treatment across every chart type"). `AppColors.chart1-3`/
/// `AppSemanticColors.chartSeries`/`chartReference` were reserved for
/// exactly this moment (see that token's own doc comment: "a real chart
/// phase... is what should justify inventing a new hue, not this phase
/// guessing ahead of it") — this component is that real phase, and uses
/// [AppSemanticColors.chartSeries]`[0]` as its one data-series color
/// rather than adding a second.
///
/// Deliberately minimal: a single primary series (e.g. a rolling
/// average), optional fainter raw points underneath it (Section 12:
/// "The rolling average is always the 'real' line; raw points are
/// context only"), an optional dashed reference/target line, a bottom
/// axis line, and per-point labels — no gridlines beyond that, no
/// gradient fill under the line, no entrance animation. Values are
/// painted directly via [CustomPainter] rather than a charting package:
/// this app has exactly one restrained chart shape to render, and a
/// hand-built painter keeps that shape under this design system's own
/// control rather than inheriting a general-purpose library's defaults
/// (legends, tooltips, animated transitions) this system's own rules
/// reject.
///
/// A canvas has no text for assistive technology to read, so
/// [semanticLabel] is required, not optional — every call site must
/// state in words what the chart shows (e.g. "Protein trend, 7 days,
/// latest 132 grams, target 130 grams") rather than leaving a screen
/// reader with nothing.
class AppLineChart extends StatelessWidget {
  const AppLineChart({
    required this.labels,
    required this.values,
    required this.semanticLabel,
    this.rawValues,
    this.referenceValue,
    this.referenceLabel,
    this.height = 160,
    super.key,
  })  : assert(
          values.length == labels.length,
          'values and labels must be the same length',
        ),
        assert(
          rawValues == null || rawValues.length == labels.length,
          'rawValues, when supplied, must be the same length as labels',
        );

  /// One label per point (e.g. weekday initials) — every point is
  /// labeled; this chart is never used with enough points that labeling
  /// all of them would be illegible.
  final List<String> labels;

  /// The primary series — a `null` entry leaves a gap rather than
  /// interpolating a value that was never recorded.
  final List<double?> values;

  /// Optional fainter points underneath [values] (e.g. each day's raw
  /// entry, when [values] is a rolling average).
  final List<double?>? rawValues;

  /// An optional horizontal guideline (e.g. a protein target, a
  /// training-load guardrail ceiling) — rendered dashed and in the
  /// neutral [AppSemanticColors.chartReference] tone so it reads as
  /// structure, never as a second data series.
  final double? referenceValue;
  final String? referenceLabel;

  final String semanticLabel;
  final double height;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;
    final TextTheme textTheme = Theme.of(context).textTheme;
    final TextStyle labelStyle = (textTheme.labelSmall ?? const TextStyle(fontSize: 11))
        .copyWith(color: colorScheme.onSurfaceVariant);

    return Semantics(
      label: semanticLabel,
      child: ExcludeSemantics(
        child: SizedBox(
          width: double.infinity,
          height: height,
          child: CustomPaint(
            painter: _AppLineChartPainter(
              labels: labels,
              values: values,
              rawValues: rawValues,
              referenceValue: referenceValue,
              referenceLabel: referenceLabel,
              lineColor: semantic.chartSeries[0],
              rawColor: colorScheme.onSurfaceVariant,
              referenceColor: semantic.chartReference,
              axisColor: colorScheme.outlineVariant,
              labelStyle: labelStyle,
            ),
          ),
        ),
      ),
    );
  }
}

class _AppLineChartPainter extends CustomPainter {
  _AppLineChartPainter({
    required this.labels,
    required this.values,
    required this.rawValues,
    required this.referenceValue,
    required this.referenceLabel,
    required this.lineColor,
    required this.rawColor,
    required this.referenceColor,
    required this.axisColor,
    required this.labelStyle,
  });

  final List<String> labels;
  final List<double?> values;
  final List<double?>? rawValues;
  final double? referenceValue;
  final String? referenceLabel;
  final Color lineColor;
  final Color rawColor;
  final Color referenceColor;
  final Color axisColor;
  final TextStyle labelStyle;

  static const double _xAxisReserve = 18;

  @override
  void paint(Canvas canvas, Size size) {
    final double plotHeight = size.height - _xAxisReserve;
    final double plotWidth = size.width;
    if (plotHeight <= 0 || plotWidth <= 0) {
      return;
    }

    final List<double> allValues = <double>[
      ...values.whereType<double>(),
      ...?rawValues?.whereType<double>(),
      if (referenceValue != null) referenceValue!,
    ];
    if (allValues.isEmpty) {
      _paintAxis(canvas, plotWidth, plotHeight);
      return;
    }

    double minV = allValues.reduce((double a, double b) => a < b ? a : b);
    double maxV = allValues.reduce((double a, double b) => a > b ? a : b);
    if (minV == maxV) {
      minV -= 1;
      maxV += 1;
    }
    final double pad = (maxV - minV) * 0.12;
    minV -= pad;
    maxV += pad;

    double xFor(int i) =>
        labels.length <= 1 ? plotWidth / 2 : plotWidth * i / (labels.length - 1);
    double yFor(double v) => plotHeight - ((v - minV) / (maxV - minV)) * plotHeight;

    _paintAxis(canvas, plotWidth, plotHeight);

    if (referenceValue != null) {
      final double ry = yFor(referenceValue!);
      _drawDashedLine(
        canvas,
        Offset(0, ry),
        Offset(plotWidth, ry),
        Paint()
          ..color = referenceColor
          ..strokeWidth = 1,
      );
      if (referenceLabel != null) {
        _paintText(
          canvas,
          referenceLabel!,
          Offset(plotWidth, (ry - 14).clamp(0, plotHeight)),
          labelStyle.copyWith(color: referenceColor),
          align: TextAlign.right,
        );
      }
    }

    if (rawValues != null) {
      // ignore: deprecated_member_use
      final Paint rawPaint = Paint()..color = rawColor.withOpacity(0.35);
      for (int i = 0; i < rawValues!.length; i++) {
        final double? v = rawValues![i];
        if (v == null) {
          continue;
        }
        canvas.drawCircle(Offset(xFor(i), yFor(v)), 2.5, rawPaint);
      }
    }

    final Path path = Path();
    bool started = false;
    final List<Offset> points = <Offset>[];
    for (int i = 0; i < values.length; i++) {
      final double? v = values[i];
      if (v == null) {
        continue;
      }
      final Offset p = Offset(xFor(i), yFor(v));
      points.add(p);
      if (!started) {
        path.moveTo(p.dx, p.dy);
        started = true;
      } else {
        path.lineTo(p.dx, p.dy);
      }
    }
    if (started) {
      canvas.drawPath(
        path,
        Paint()
          ..color = lineColor
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke
          ..strokeJoin = StrokeJoin.round
          ..strokeCap = StrokeCap.round,
      );
      final Paint dotPaint = Paint()..color = lineColor;
      for (final Offset p in points) {
        canvas.drawCircle(p, 2.5, dotPaint);
      }
    }

    for (int i = 0; i < labels.length; i++) {
      _paintText(
        canvas,
        labels[i],
        Offset(xFor(i), plotHeight + 4),
        labelStyle,
        align: TextAlign.center,
      );
    }
  }

  void _paintAxis(Canvas canvas, double width, double height) {
    canvas.drawLine(
      Offset(0, height),
      Offset(width, height),
      Paint()
        ..color = axisColor
        ..strokeWidth = 1,
    );
  }

  void _paintText(
    Canvas canvas,
    String text,
    Offset anchor,
    TextStyle style, {
    TextAlign align = TextAlign.left,
  }) {
    final TextPainter painter = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
      textAlign: align,
    )..layout();
    double dx = anchor.dx;
    if (align == TextAlign.center) {
      dx -= painter.width / 2;
    } else if (align == TextAlign.right) {
      dx -= painter.width;
    }
    painter.paint(canvas, Offset(dx, anchor.dy));
  }

  void _drawDashedLine(Canvas canvas, Offset start, Offset end, Paint paint) {
    const double dashWidth = 4;
    const double dashSpace = 4;
    final double totalLength = (end - start).distance;
    if (totalLength == 0) {
      return;
    }
    final Offset direction = (end - start) / totalLength;
    double drawn = 0;
    while (drawn < totalLength) {
      final double segment =
          (drawn + dashWidth > totalLength) ? totalLength - drawn : dashWidth;
      canvas.drawLine(
        start + direction * drawn,
        start + direction * (drawn + segment),
        paint,
      );
      drawn += dashWidth + dashSpace;
    }
  }

  @override
  bool shouldRepaint(covariant _AppLineChartPainter oldDelegate) {
    return oldDelegate.values != values ||
        oldDelegate.rawValues != rawValues ||
        oldDelegate.referenceValue != referenceValue ||
        oldDelegate.labels != labels ||
        oldDelegate.lineColor != lineColor;
  }
}
