# API Rate Limiter

Educational rate limiting middleware for Go HTTP servers. It implements token-bucket and leaky-bucket algorithms as configurable middleware, and ships a CLI to configure and test rate limits.

## Educational Purpose

**Important:** This tool is intended solely for educational and authorized testing purposes. Rate limiting is a fundamental HTTP security pattern. This tool should only be used on HTTP servers you own or have explicit written permission to test.

### Authorized Use Only

- Only apply rate limiting to HTTP endpoints you own or have explicit permission to test
- Obtain explicit written permission before testing any rate limiting configuration
- Report any discovered issues to the appropriate system owner
- Never apply rate limiting to endpoints you do not have explicit authorization for

### Educational Value

Understanding rate limiting helps development teams:
- Implement proper API protection mechanisms
- Design appropriate rate limit parameters for their use cases
- Test rate limiting behavior before production deployment
- Educate team members about API security practices

### Legal Compliance

- Unauthorized rate limiting may violate terms of service of API providers
- Follow institutional policies regarding API testing tools
- Always obtain explicit written permission before testing any rate limiting configuration

### Responsible Use

- This project is provided for educational purposes only
- Results should be verified with proper security tools for real-world use
- Never use discovered techniques against production systems without authorization

## License

MIT - This project is free software: you can redistribute it and/or modify it under the terms of the MIT License. See the LICENSE file for full terms and conditions.