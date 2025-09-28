# Security Policy

## Supported Versions

We provide security updates for the following versions of skoglib:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Built-in Security Measures

- **Input Validation**: All executable paths and arguments are validated before execution
- **Path Sanitization**: Prevents path traversal and injection attacks
- **Secure Defaults**: Conservative security settings by default
- **Error Handling**: Secure error messages that don't leak sensitive information
- **Logging**: Security-conscious logging that avoids sensitive data exposure

### CI/CD Security

Our development pipeline includes comprehensive security measures:

- **Static Application Security Testing (SAST)**: Bandit scans for security vulnerabilities
- **Dependency Scanning**: Regular vulnerability checks using pip-audit
- **Supply Chain Security**: Package integrity verification and suspicious package detection
- **Secrets Detection**: TruffleHog scans for accidentally committed secrets
- **Automated Updates**: Dependabot provides timely security updates

## Reporting a Vulnerability

If you discover a security vulnerability in skoglib, please report it responsibly:

### How to Report

1. **Do NOT create a public GitHub issue** for security vulnerabilities
2. Send an email to: **security@skogai.com**
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 24 hours
- **Initial Assessment**: We will provide an initial assessment within 72 hours
- **Regular Updates**: We will send updates every 7 days during investigation
- **Resolution Timeline**: We aim to resolve critical vulnerabilities within 30 days

### Security Response Process

1. **Vulnerability Assessment**: We evaluate the severity and impact
2. **Fix Development**: We develop and test a security fix
3. **Security Advisory**: We prepare a security advisory (if applicable)
4. **Coordinated Disclosure**: We coordinate release timing with the reporter
5. **Public Disclosure**: We publish the fix and advisory simultaneously

## Security Best Practices

When using skoglib in your projects:

### Safe Usage Guidelines

```python
from skoglib import run_executable

# ✅ Good: Use explicit arguments
result = run_executable('ls', ['-la', '/safe/path'])

# ❌ Avoid: Shell injection risks
# Don't construct commands from user input without validation
user_input = get_user_input()  # Could be malicious
result = run_executable('sh', ['-c', user_input])  # Dangerous!

# ✅ Better: Validate and sanitize user input
if is_safe_command(user_input):
    result = run_executable('sh', ['-c', user_input])
```

### Environment Security

- **Principle of Least Privilege**: Run with minimal required permissions
- **Input Validation**: Always validate user inputs before passing to skoglib
- **Path Restrictions**: Limit executable paths to known safe directories
- **Timeout Settings**: Use appropriate timeouts to prevent resource exhaustion
- **Error Handling**: Handle exceptions securely without exposing sensitive details

### Production Deployment

- **Regular Updates**: Keep skoglib updated to the latest version
- **Dependency Monitoring**: Monitor dependencies for known vulnerabilities
- **Logging Configuration**: Configure logging appropriately for your security requirements
- **Resource Limits**: Set appropriate resource limits for subprocess execution
- **Network Security**: Consider network restrictions for executable operations

## Security Updates

### Notification Channels

Stay informed about security updates:

- **GitHub Security Advisories**: Watch the repository for security advisories
- **Release Notes**: Check release notes for security-related changes
- **Email Notifications**: Subscribe to security update notifications

### Update Process

When security updates are available:

1. **Review the Advisory**: Understand the vulnerability and impact
2. **Test in Staging**: Test the update in a non-production environment
3. **Deploy Promptly**: Apply security updates as soon as possible
4. **Verify Fix**: Confirm the vulnerability is resolved

## Compliance and Standards

skoglib follows industry security standards:

- **OWASP Guidelines**: We follow OWASP secure coding practices
- **Python Security**: We adhere to Python security recommendations
- **Supply Chain Security**: We implement SLSA (Supply-chain Levels for Software Artifacts) practices
- **Vulnerability Disclosure**: We follow responsible disclosure practices

## Security Contact

For security-related questions or concerns:

- **Email**: security@skogai.com
- **GPG Key**: Available upon request
- **Response Time**: 24-48 hours for initial response

## Hall of Fame

We recognize security researchers who help improve skoglib's security:

<!-- Security researchers who have reported vulnerabilities will be listed here -->

---

Last updated: January 2025
Next review: April 2025