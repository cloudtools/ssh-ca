## 0.3.1 (2014-04-17)
- remove the private key first if we already have a cert loaded prior to
  adding it to the agent

## 0.3.0 (2014-04-07)
- Support specifying the principals in use
- Add functionality for signing host keys
- Add testing via travis-ci

## 0.2.0 (2014-02-25)
- Add environment-specific public keys
- Run ssh-add as part of get cert so openssh will detect the new cert
- For auditing, require that a reason be specified when signing

## 0.1.0 (2014-02-04)
- First PyPI release
