# Security Policy

## Supported Versions

I actively support version 1.0.x and above.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

## Reporting a Vulnerability

### Security Concerns

If you discover a security vulnerability in this integration, please handle it responsibly:

1. **Do NOT** open a public issue
2. **Do NOT** disclose the vulnerability publicly until it has been addressed

### How to Report

To report a security problem:

1. Go to [Security Advisories](https://github.com/dsorlov/smartthingsce/security/advisories)
2. Click "Report a vulnerability"
3. Provide detailed information about the vulnerability:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

Alternatively, you can email security concerns directly to the maintainer.

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Regular Updates**: Every 5-7 days until resolved
- **Resolution**: Security issues are prioritized and will be addressed as quickly as possible

### Security Best Practices

When using this integration:

1. **Protect Your Token**: Never share your SmartThings Personal Access Token
2. **Use HTTPS**: Ensure your Home Assistant instance uses HTTPS
3. **Keep Updated**: Always use the latest version of the integration
4. **Monitor Access**: Regularly review your SmartThings token permissions
5. **Webhook Security**: The localtunnel provides encrypted communication, but be aware it creates an externally accessible endpoint

### Token Security

- Tokens are stored encrypted in Home Assistant's configuration
- Tokens are never logged or exposed in debug output
- Revoke tokens immediately if you suspect compromise
- Use minimum required token scopes

### Webhook Security

- Webhook endpoints use unique, randomly generated identifiers
- All webhook communication is encrypted via HTTPS
- Webhook signatures should be validated (future enhancement)
- Webhooks are automatically cleaned up when integration is removed

## Disclosure Policy

When a security vulnerability is fixed:

1. A security advisory will be published
2. Users will be notified through GitHub
3. A new release will be created with the fix
4. The CHANGELOG will include security-related changes
5. Credit will be given to the reporter (if desired)

Thank you for helping keep SmartThings Community Edition secure! 🔒
