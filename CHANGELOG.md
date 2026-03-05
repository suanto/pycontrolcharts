# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Versioning: Package version is now derived from Git tags via [setuptools-scm](https://setuptools-scm.readthedocs.io/) at build time. 

## [0.1.1] - 2025-03-01

### Changed

- Plotting: increased vertical spacing between main and variation subplots.

## [0.1.0] - 2025-02-27

### Added

- Initial release.
- Variable charts: XmR (Individuals and Moving Range), X-bar/R, X-bar/S.
- Attribute charts: p-chart, np-chart, c-chart, u-chart.
- Run tests (Nelson rules, configurable); violation type codes and descriptions.
- Multi-phase control limits and specification limits (single value, list, or DataFrame column).
- Variable subgroup sizes for X-bar/R and X-bar/S.
- Custom limits support for applying run tests to pre-computed limits.
- Optional Plotly plotting for all chart types.
- Export to CSV, Excel, and JSON.
- Pandas integration: single DataFrame output with limits, violations, phases, and optional spec limits.
- Full type hints; Python 3.10+.
