# AdguardSync

This script syncs the DNS-Rewrite list with the given config file.

Example:
```python
>>> from adguard_sync import AdguardSync
>>> AdguardSync('config.yml')
```

Configuration File:
```yaml
---

adguards:
  - hostname: https://10.0.0.3
    username: adguard
    password: adguard_pass
    verify_ssl: False # (Optional, default = True)
  - hostname: https://10.0.0.4
    username: adguard
    password: adguard_pass

dns_records:
  - domain: adguard.test
    address: 10.0.0.3
  - domain: adguard2.test
    address: 10.0.0.4
```