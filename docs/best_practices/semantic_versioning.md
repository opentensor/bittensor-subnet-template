# Semantic Versioning (SemVer) for Subnet Owners

Semantic Versioning, or SemVer, is a versioning scheme that helps users understand the impact of updates and ensures compatibility. This guide will explain how to implement SemVer effectively in your Bittensor subnet.

## Version Format

Use the MAJOR.MINOR.PATCH format (e.g., 1.2.3). Each number has a specific meaning:

- MAJOR: Incompatible API changes
- MINOR: New functionality in a backwards-compatible manner
- PATCH: Backwards-compatible bug fixes

## Increment Rules

1. MAJOR version: Increment when you make incompatible API changes.
2. MINOR version: Increment when you add functionality in a backwards-compatible manner.
3. PATCH version: Increment when you make backwards-compatible bug fixes.

## Pre-release Versions

For pre-release versions, use labels after the PATCH version, separated by a hyphen:

- Alpha: 1.0.0-alpha.1
- Beta: 1.0.0-beta.1
- Release Candidate: 1.0.0-rc.1

## Maintaining Version in Code

Keep a version variable in your code and update it with each release. For example, in Python:

```python
__version__ = "1.2.3"
```

Present the version to the user in a human-readable format, such as:

```
Your subnet N neuron in validator mode is running version 1.2.3
```

Don't be afraid to be transparent about the version. Users appreciate knowing exactly what they're running. Add it to logs, and print it out in the console when the neuron starts up. 

## Changelog

Maintain a detailed CHANGELOG.md file to document changes between versions. Include:

- Version number and release date
- List of new features
- Bug fixes
- Breaking changes

## Git Tags

Tag your releases in Git using the version number. This helps with tracking and deploying specific versions:

```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

## Git Repository and Docker Image Tag Consistency

Ensure that your Git repository tags and Docker Hub image tags are consistent. This practice helps users and developers easily identify and use the correct version of your subnet.

1. When you create a new release:
   - Tag your Git repository with the version number
   - Build and push a Docker image with the same tag

2. Example workflow:
   
```bash
# Tag Git repository
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Build and push Docker image
docker build -t your-dockerhub-username/your-subnet:v1.2.3 .
docker push your-dockerhub-username/your-subnet:v1.2.3
```

3. Always use specific version tags for production deployments, rather than the `latest` tag.

By following these semantic versioning practices, you'll provide clear information about your subnet's development progress and help users manage dependencies effectively. Remember to communicate any breaking changes clearly in your documentation and release notes.