# Screenshots

**No screenshots exist yet.** This directory is a placeholder — `flutter analyze`/`flutter test`
now run clean (`docs/adr/0002`'s "Update" note), and `android`/`ios` platform folders are
committed, but the app itself has never been run on a real device or simulator, so there is
nothing genuine to capture. This file exists so the expected set is decided in advance, and so
the root `README.md`'s screenshots section has something real to link to the moment images land
here, instead of an `<img>` tag pointing at a file that was never added.

## TODO — capture once a real build exists

Once `flutter run` works on a real device/simulator (see `docs/RELEASE_PROCESS.md` for what
else that depends on), capture one light-mode screenshot per primary screen, saved as
`docs/screenshots/<screen-name>.png` (1080px-wide portrait, matching the device frame style, no
personal data visible):

| File | Screen | Notes |
|---|---|---|
| `today.png` | Today (`TodayScreen`) | The default landing tab — session card in its `ready` state. |
| `train-home.png` | Train Home (`TrainHomeScreen`) | "This Week" tab selected. |
| `active-workout.png` | Active Workout (`ActiveWorkoutScreen`) | Mid-session, at least one set logged. |
| `fuel-home.png` | Fuel Home (`FuelHomeScreen`) | With at least one logged meal visible. |
| `progress-home.png` | Progress Home (`ProgressHomeScreen`) | Transformation segment with a real trend chart. |
| `readiness-checkin.png` | Readiness Check-in (`ReadinessCheckInScreen`) | Mid-form. |
| `coach-home.png` | Coach Home (`CoachHomeScreen`) | With at least one real signal in the feed. |
| `dark-mode.png` | Any screen above | One dark-mode example, to show the theme exists. |

## TODO — demo GIF

A short (10–20s) screen recording of the primary daily-loop flow — Today → Start session →
Active Workout → log a set → Session Summary — converted to an optimized GIF or WebP
(`docs/screenshots/demo.gif`), for the root README's hero section. Capture with the OS's
built-in screen recorder or `flutter screenshot`/`simctl io recordVideo`, then compress with
`gifski` or `ffmpeg` before committing (GitHub renders GIFs inline, but large, uncompressed
captures bloat the repository).

Until both exist, the root `README.md` says so plainly rather than embedding a broken image
link.
