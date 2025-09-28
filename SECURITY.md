# Security Policy

## Supported Versions

The following versions of skoglib are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

The SkogAI team takes security seriously. If you discover a security vulnerability in skoglib, please report it responsibly.

### How to Report

1. **Email**: Send details to security@skogai.com
2. **GitHub Security Advisories**: Use GitHub's private vulnerability reporting feature
3. **Encrypted Communication**: Contact maintainers for PGP keys if needed

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and attack scenarios
- Suggested fixes or mitigations (if any)
- Your contact information

### Response Timeline

- **Initial Response**: Within 48 hours
- **Investigation**: Within 7 days
- **Fix Release**: Within 30 days for critical issues, 90 days for others
- **Public Disclosure**: After fix is released and users have time to update

### Vulnerability Disclosure Process

1. **Private Report**: Vulnerability reported privately
2. **Acknowledgment**: We confirm receipt and begin investigation
3. **Assessment**: We evaluate the impact and severity
4. **Fix Development**: We develop and test a fix
5. **Release**: Security fix is released
6. **Disclosure**: Public disclosure after users have time to update

## Security Considerations

### Subprocess Execution

skoglib executes external commands through Python's `subprocess` module. While we implement security best practices, users should be aware that:

- Never pass untrusted input directly to `run_executable()`
- Validate and sanitize all user inputs before execution
- Be cautious with shell metacharacters in arguments
- Use absolute paths for executables when possible

### Environment Variables

When using environment variables:

- Avoid passing sensitive data through environment variables
- Be aware that environment variables may be logged or visible to other processes
- Use secure secret management systems for sensitive configuration

### File System Access

- The library respects working directory changes
- Be cautious with relative paths in untrusted environments
- Ensure proper file permissions on executables and working directories

## Security Best Practices for Users

1. **Input Validation**: Always validate inputs before passing to skoglib functions
2. **Principle of Least Privilege**: Run with minimal required permissions
3. **Path Validation**: Use absolute paths or validate PATH contents
4. **Error Handling**: Don't expose sensitive information in error messages
5. **Logging**: Be careful not to log sensitive information

## Security Scanning

This project uses automated security scanning:

- **Static Analysis**: Bandit for Python security issues
- **Dependency Scanning**: Safety for known vulnerabilities
- **Supply Chain**: Verification of dependency integrity

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors will be acknowledged in release notes unless they prefer to remain anonymous.

## Contact

For security-related questions or concerns:
- Email: security@skogai.com
- GitHub: Create a private security advisory

For general questions about skoglib:
- GitHub Issues: For non-security bugs and feature requests
- GitHub Discussions: For questions and community discussion
