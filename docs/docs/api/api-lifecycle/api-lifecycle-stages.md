---
description: "Dagster's public, stable API adheres to semantic versioning and won't break within any major release."
sidebar_position: 100
title: API lifecycle stages
---

This reference guide outlines the different stages in the lifecycle of Dagster APIs, from preview to deprecation. Understanding these stages helps you make informed decisions about which APIs to use in your projects, based on your specific needs for stability, feature completeness, and long-term support.

Dagster's API lifecycle is designed to balance innovation with stability, ensuring that you can rely on consistent behavior while also benefiting from new features and improvements. This approach allows Dagster to evolve and adapt to changing requirements in the data engineering landscape while maintaining a stable foundation for existing projects.

## API lifecycle stages

| Stage                    | Description                                                                                                            | Lifetime                                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Preview                  | This API may have breaking changes in patch version releases. This feature is not considered ready for production use. | Until design is complete, or implementation canceled.                                                                 |
| Beta                     | This API may have breaking changes in minor version releases, with behavior changes in patch releases.                 | At most, two 1.x releases before it is either considered stable or returned to preview.                               |
| Generally Available (GA) | Ready for production use, with minimal risk of breaking changes.                                                       | Supported until at least 2.0                                                                                          |
| Superseded               | This API is still available, but is no longer the best practice. A better alternative is available.                    | Supported until at least 2.0                                                                                          |
| Deprecated               | This API is still available, but will be removed in the future; avoid new usage.                                       | Will be removed in a minor release. The `DeprecationWarning` will indicate the next release that will remove the API. |

## Understanding the stages

### Preview

- **Purpose**: Early testing and feedback.
- **Stability**: Highly unstable, expect frequent changes.
- **Usage**: Not recommended for production environments.
- **Documentation**: Minimal, typically a README, unlisted documentation, or pages in the [Labs section](/guides/labs).

### Beta

- **Purpose**: Feature testing with a wider audience.
- **Stability**: More stable than Preview, but still subject to change.
- **Usage**: Can be used in non-critical production environments.
- **Documentation**: How-to guides and API documentation available.

### GA (General Availability)

- **Purpose**: Production-ready features.
- **Stability**: Stable with minimal risk of breaking changes.
- **Usage**: Recommended for all production environments.
- **Documentation**: Comprehensive documentation available.

### Superseded

- **Purpose**: Maintains backwards compatibility while promoting newer alternatives.
- **Stability**: Stable, but no longer recommended.
- **Usage**: Existing implementations can continue, but new projects should use the recommended alternative.
- **Documentation**: API docs remain, but usage is discouraged in favor of newer alternatives.

### Deprecated

- **Purpose**: Signals upcoming removal of the API.
- **Stability**: Stable, but scheduled for removal.
- **Usage**: Existing implementations should plan migration.
- **Documentation**: API docs remain, with clear warnings about deprecation. Arguments may be removed from function signature.
