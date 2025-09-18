# Sensitive Data Redaction

## Overview

The framework automatically redacts sensitive data from API requests, responses, console logs, and test reports to protect credentials and personally identifiable information (PII) in test evidence.

## How It Works

### Integration Points

The redaction system integrates at multiple levels in the API flow:

```
Test Code → BaseAPI → ApiExecutor → APIRecorder → Reports
                          ↑
                    DataRedactor
                  (redacts all data)
```

### Flow Diagram

1. **Test makes API call** through your API classes (AuthAPI, etc.)
2. **BaseAPI calls ApiExecutor** with request data
3. **ApiExecutor intercepts** all data before logging/recording
4. **DataRedactor scans** for sensitive patterns and field names
5. **Redacted data flows** to console logs, Allure reports, HTML reports
6. **Original data preserved** for actual API calls (not redacted in flight)

### What Gets Redacted

**Field Names (case-insensitive):**
- `password`, `passwd`, `pwd`
- `secret`, `token`, `key`
- `auth`, `authorization`, `credential`
- `pin`, `ssn`, `social_security`
- `credit_card`, `creditcard`, `cc_number`, `cvv`
- `access_token`, `refresh_token`, `id_token`
- `session_id`, `api_key`, `private_key`

**Value Patterns:**
- Base64-like strings (20+ chars): `dGVzdDEyMzQ1Njc4OTA=`
- Bearer tokens: `Bearer abc123xyz789`
- Basic auth: `Basic dXNlcjpwYXNz`
- Credit card numbers: `1234-5678-9012-3456`
- SSN format: `123-45-6789`

### Where Redaction Applies

**Console Logs:**
```bash
🚀 API REQUEST [MOCK]
   Headers: {
     "Authorization": "***REDACTED***"
   }
   Body: {
     "username": "testuser",
     "password": "***REDACTED***"
   }
```

**Allure Reports:**
- Request/Response JSON attachments
- PNG screenshots of API data

**HTML Reports:**
- API trace reports
- Per-worker reports

**Failure Logs:**
- Last API response on test failures

### Important Notes

- **Redaction is display-only** - actual API calls use original unredacted data
- **Thread-safe** - works correctly in parallel test execution
- **Recursive** - redacts nested objects and arrays
- **Configurable** - can be enabled/disabled per environment

## Configuration

### Default Behavior
Redaction is **enabled by default** for security.

### Disable Redaction

**Option 1: Environment Variable**
```bash
# Disable for entire test run
REDACT_SENSITIVE_DATA=false pytest

# Enable (default)
REDACT_SENSITIVE_DATA=true pytest
```

**Option 2: Settings File**
```python
# src/config/settings.py
class Settings:
    # Disable redaction
    redact_sensitive_data = False
    
    # Enable redaction (default)
    redact_sensitive_data = True
```

**Option 3: Runtime Check**
```python
# In your test or conftest
if os.getenv('TEST_ENV') == 'dev':
    settings.redact_sensitive_data = False  # Show real data in dev
```

### Precedence Order
1. Settings file value (`settings.redact_sensitive_data`)
2. Environment variable (`REDACT_SENSITIVE_DATA`)
3. Default (enabled)

Either source can enable redaction. Both must disable it to turn it off.

## Customization

### Add Custom Sensitive Fields
```python
# Modify the DataRedactor in ApiExecutor
custom_fields = DataRedactor.DEFAULT_SENSITIVE_FIELDS.copy()
custom_fields.update({'custom_secret', 'internal_token'})

redactor = DataRedactor(sensitive_fields=custom_fields)
```

### Custom Redaction Text
```python
redactor = DataRedactor(redaction_text="[HIDDEN]")
```

### Custom Value Patterns
```python
# Add custom regex patterns for sensitive values
custom_patterns = DataRedactor.SENSITIVE_VALUE_PATTERNS.copy()
custom_patterns.append(r'^CUSTOM_[A-Z0-9]{10}$')  # Custom ID format
```

## Examples

### Before Redaction
```json
{
  "username": "testuser",
  "password": "mySecretPassword123",
  "authorization": "Bearer eyJhbGciOiJIUzI1NiIs...",
  "user_data": {
    "ssn": "123-45-6789",
    "credit_card": "4532-1234-5678-9012"
  }
}
```

### After Redaction
```json
{
  "username": "testuser", 
  "password": "***REDACTED***",
  "authorization": "***REDACTED***",
  "user_data": {
    "ssn": "***REDACTED***",
    "credit_card": "***REDACTED***"
  }
}
```

## Troubleshooting

### Redaction Not Working
- Check `REDACT_SENSITIVE_DATA` environment variable
- Verify `settings.redact_sensitive_data` value
- Ensure ApiExecutor is using the updated version

### Data Still Showing
- Field name might not match patterns (add custom fields)
- Value might not match regex patterns (add custom patterns)
- Check if data is coming from a different code path

### Performance Impact
- Redaction adds minimal overhead (regex matching)
- Only applies to logging/reporting, not actual API calls
- Can be disabled in performance-critical environments

## Best Practices

1. **Leave enabled in CI/CD** - Protects credentials in build logs
2. **Disable in local dev** - When you need to debug actual values
3. **Review patterns** - Add custom patterns for your specific data types
4. **Test with real data** - Verify redaction works with your actual API responses
5. **Document exceptions** - If you disable redaction, document why